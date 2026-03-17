"""Finance reconciliation suite for FMCG sales data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ReconciliationRule:
    """A single reconciliation check applied row-wise to a DataFrame."""

    name: str
    check: Callable[[pd.DataFrame], pd.Series]
    tolerance: float = 0.0
    description: str = ""


@dataclass
class ReconciliationReport:
    """Results of running one :class:`ReconciliationRule` on a DataFrame."""

    rule_name: str
    total_rows: int
    passed_rows: int
    failed_rows: int
    failed_indices: list[int] = field(default_factory=list)
    tolerance: float = 0.0


class ReconciliationSuite:
    """Ordered collection of :class:`ReconciliationRule` objects."""

    def __init__(self) -> None:
        self._rules: list[ReconciliationRule] = []

    def add_rule(self, rule: ReconciliationRule) -> None:
        self._rules.append(rule)

    def run(self, df: pd.DataFrame) -> list[ReconciliationReport]:
        """Execute every rule against *df* and return a list of reports."""
        reports: list[ReconciliationReport] = []
        for rule in self._rules:
            passed_mask = rule.check(df)
            failed_idx = df.index[~passed_mask].tolist()
            reports.append(ReconciliationReport(
                rule_name=rule.name,
                total_rows=len(df),
                passed_rows=int(passed_mask.sum()),
                failed_rows=int((~passed_mask).sum()),
                failed_indices=failed_idx,
                tolerance=rule.tolerance,
            ))
        return reports

    @staticmethod
    def summary(reports: list[ReconciliationReport]) -> dict[str, dict[str, object]]:
        """Return a compact dict mapping rule names to pass-rate summaries."""
        return {
            r.rule_name: {
                "total_rows": r.total_rows,
                "passed_rows": r.passed_rows,
                "failed_rows": r.failed_rows,
                "pass_rate": round(r.passed_rows / r.total_rows, 4) if r.total_rows else 0.0,
                "tolerance": r.tolerance,
            }
            for r in reports
        }

    def list_rules(self) -> list[ReconciliationRule]:
        return list(self._rules)


# ---------------------------------------------------------------------------
# Pre-registered rules
# ---------------------------------------------------------------------------

def _gross_sales_check(df: pd.DataFrame) -> pd.Series:
    expected = df["units_sold"] * df["list_price"]
    return (df["gross_sales"] - expected).abs() <= 0.01


def _net_sales_check(df: pd.DataFrame) -> pd.Series:
    expected = df["gross_sales"] * (1 - df["discount_pct"])
    return (df["net_sales"] - expected).abs() <= 0.02


def _margin_pct_check(df: pd.DataFrame) -> pd.Series:
    """Reconcile margin_pct = (net_sales - purchase_cost * units_sold) / net_sales."""
    cogs = df["purchase_cost"] * df["units_sold"]
    net = df["net_sales"]
    # Guard against division by zero: treat net==0 rows as passing
    safe_net = net.replace(0, np.nan)
    expected = (net - cogs) / safe_net
    diff = (df["margin_pct"] - expected).abs()
    return diff.fillna(0) <= 0.02


def _non_negative_units(df: pd.DataFrame) -> pd.Series:
    return df["units_sold"] >= 0


def _positive_list_price(df: pd.DataFrame) -> pd.Series:
    return df["list_price"] > 0


def _discount_range(df: pd.DataFrame) -> pd.Series:
    return (df["discount_pct"] >= 0) & (df["discount_pct"] <= 1)


def _stock_on_hand_non_negative(df: pd.DataFrame) -> pd.Series:
    return df["stock_on_hand"] >= 0


def default_reconciliation_suite() -> ReconciliationSuite:
    """Factory returning a :class:`ReconciliationSuite` with standard FMCG finance rules."""
    suite = ReconciliationSuite()
    suite.add_rule(ReconciliationRule(
        "gross_sales_reconciliation", _gross_sales_check, 0.01,
        "abs(gross_sales − units_sold × list_price) ≤ 0.01",
    ))
    suite.add_rule(ReconciliationRule(
        "net_sales_reconciliation", _net_sales_check, 0.02,
        "abs(net_sales − gross_sales × (1 − discount_pct)) ≤ 0.02",
    ))
    suite.add_rule(ReconciliationRule(
        "margin_pct_reconciliation", _margin_pct_check, 0.02,
        "abs(margin_pct − (net_sales − COGS) / net_sales) ≤ 0.02",
    ))
    suite.add_rule(ReconciliationRule(
        "non_negative_units", _non_negative_units, 0.0,
        "units_sold ≥ 0",
    ))
    suite.add_rule(ReconciliationRule(
        "positive_list_price", _positive_list_price, 0.0,
        "list_price > 0",
    ))
    suite.add_rule(ReconciliationRule(
        "discount_range", _discount_range, 0.0,
        "0 ≤ discount_pct ≤ 1",
    ))
    suite.add_rule(ReconciliationRule(
        "stock_on_hand_non_negative", _stock_on_hand_non_negative, 0.0,
        "stock_on_hand ≥ 0",
    ))
    return suite
