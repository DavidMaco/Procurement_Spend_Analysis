"""Variance alerting engine for FMCG commercial and procurement metrics.

Detects when KPIs or row-level metrics deviate beyond configurable thresholds
from a baseline period, and emits structured alerts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional
from uuid import uuid4

import pandas as pd


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertCategory(str, Enum):
    COMMERCIAL = "commercial"
    PROCUREMENT = "procurement"


@dataclass(frozen=True)
class VarianceRule:
    """Declarative rule that fires when a metric's variance exceeds a threshold."""

    name: str
    metric_column: str
    category: AlertCategory
    threshold_pct: float
    metric_fn: Optional[Callable[[pd.DataFrame], pd.Series]] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    aggregation: str = "mean"  # "mean" | "sum" | "median"
    group_by: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Alert:
    """A single fired alert instance."""

    alert_id: str
    rule_name: str
    category: str
    severity: str
    metric_column: str
    baseline_value: float
    current_value: float
    variance_pct: float
    threshold_pct: float
    group_key: Optional[dict[str, str]]
    fired_at: str
    message: str


class VarianceAlertEngine:
    """Evaluates :class:`VarianceRule` objects against baseline and current data."""

    def __init__(self) -> None:
        self._rules: list[VarianceRule] = []

    def add_rule(self, rule: VarianceRule) -> None:
        self._rules.append(rule)

    def list_rules(self) -> list[VarianceRule]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
    ) -> list[Alert]:
        """Compare *current_df* against *baseline_df* and return fired alerts."""
        alerts: list[Alert] = []
        now = datetime.now(timezone.utc).isoformat()

        for rule in self._rules:
            if rule.group_by:
                alerts.extend(
                    self._evaluate_grouped(rule, baseline_df, current_df, now)
                )
            else:
                alert = self._evaluate_scalar(rule, baseline_df, current_df, now)
                if alert is not None:
                    alerts.append(alert)

        return alerts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _agg(series: pd.Series, method: str) -> float:
        if method == "sum":
            return float(series.sum())
        if method == "median":
            return float(series.median())
        return float(series.mean())

    @staticmethod
    def _metric_values(rule: VarianceRule, df: pd.DataFrame) -> pd.Series:
        if rule.metric_fn is not None:
            return rule.metric_fn(df)
        return df[rule.metric_column]

    def _evaluate_scalar(
        self,
        rule: VarianceRule,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        now: str,
    ) -> Optional[Alert]:
        base_val = self._agg(self._metric_values(rule, baseline_df), rule.aggregation)
        curr_val = self._agg(self._metric_values(rule, current_df), rule.aggregation)
        return self._maybe_fire(rule, base_val, curr_val, None, now)

    def _evaluate_grouped(
        self,
        rule: VarianceRule,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        now: str,
    ) -> list[Alert]:
        alerts: list[Alert] = []
        baseline_metrics = baseline_df.assign(
            _metric_value=self._metric_values(rule, baseline_df)
        )
        current_metrics = current_df.assign(
            _metric_value=self._metric_values(rule, current_df)
        )
        base_agg = baseline_metrics.groupby(rule.group_by)["_metric_value"].agg(
            rule.aggregation
        )
        curr_agg = current_metrics.groupby(rule.group_by)["_metric_value"].agg(
            rule.aggregation
        )

        for key in curr_agg.index:
            if key not in base_agg.index:
                continue
            group_dict = (
                dict(zip(rule.group_by, key))
                if isinstance(key, tuple)
                else {rule.group_by[0]: key}
            )
            alert = self._maybe_fire(
                rule,
                float(base_agg[key]),
                float(curr_agg[key]),
                group_dict,
                now,
            )
            if alert is not None:
                alerts.append(alert)
        return alerts

    @staticmethod
    def _maybe_fire(
        rule: VarianceRule,
        base_val: float,
        curr_val: float,
        group_key: Optional[dict[str, str]],
        now: str,
    ) -> Optional[Alert]:
        if base_val == 0 or not math.isfinite(base_val) or not math.isfinite(curr_val):
            return None
        variance_pct = (curr_val - base_val) / abs(base_val) * 100
        if abs(variance_pct) < rule.threshold_pct:
            return None
        direction = "increased" if variance_pct > 0 else "decreased"
        msg = (
            f"{rule.metric_column} {direction} by {abs(variance_pct):.1f}% "
            f"(baseline={base_val:.2f}, current={curr_val:.2f})"
        )
        return Alert(
            alert_id=uuid4().hex[:12],
            rule_name=rule.name,
            category=rule.category.value,
            severity=rule.severity.value,
            metric_column=rule.metric_column,
            baseline_value=round(base_val, 4),
            current_value=round(curr_val, 4),
            variance_pct=round(variance_pct, 2),
            threshold_pct=rule.threshold_pct,
            group_key=group_key,
            fired_at=now,
            message=msg,
        )


# ---------------------------------------------------------------------------
# Factory with default rules
# ---------------------------------------------------------------------------


def default_variance_engine() -> VarianceAlertEngine:
    """Return an engine pre-loaded with standard commercial + procurement rules."""
    engine = VarianceAlertEngine()

    def _gross_to_net_leakage(df: pd.DataFrame) -> pd.Series:
        if "gross_sales" not in df.columns or "net_sales" not in df.columns:
            return pd.Series(float("nan"), index=df.index, dtype=float)
        gross = df["gross_sales"].replace(0, float("nan"))
        return (df["gross_sales"] - df["net_sales"]) / gross

    # Commercial rules
    engine.add_rule(
        VarianceRule(
            name="gross_to_net_leakage_spike",
            metric_column="gross_to_net_leakage",
            category=AlertCategory.COMMERCIAL,
            threshold_pct=15.0,
            metric_fn=_gross_to_net_leakage,
            severity=AlertSeverity.WARNING,
            aggregation="mean",
            group_by=["category"],
            description="Alert when gross-to-net leakage rises >15% vs baseline by category",
        )
    )
    engine.add_rule(
        VarianceRule(
            name="net_sales_drop",
            metric_column="net_sales",
            category=AlertCategory.COMMERCIAL,
            threshold_pct=10.0,
            severity=AlertSeverity.CRITICAL,
            aggregation="sum",
            description="Alert when total net sales drop >10% vs baseline",
        )
    )

    # Procurement rules
    engine.add_rule(
        VarianceRule(
            name="purchase_cost_increase",
            metric_column="purchase_cost",
            category=AlertCategory.PROCUREMENT,
            threshold_pct=5.0,
            severity=AlertSeverity.WARNING,
            aggregation="mean",
            group_by=["supplier_id"],
            description="Alert when avg purchase cost rises >5% by supplier",
        )
    )
    engine.add_rule(
        VarianceRule(
            name="lead_time_deterioration",
            metric_column="lead_time_days",
            category=AlertCategory.PROCUREMENT,
            threshold_pct=20.0,
            severity=AlertSeverity.WARNING,
            aggregation="mean",
            group_by=["supplier_id"],
            description="Alert when avg lead time worsens >20% by supplier",
        )
    )

    return engine
