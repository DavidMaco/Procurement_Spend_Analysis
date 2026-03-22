"""KPI catalog for FMCG Revenue and Procurement OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd


@dataclass(frozen=True)
class KPI:
    """Declarative KPI definition."""

    id: str
    name: str
    formula_str: str
    formula_func: Callable[..., float]
    category: str  # "commercial" | "procurement" | "shared"
    owner: str = "TBD"
    cadence: str = "monthly"
    description: str = ""


class KPICatalog:
    """Registry of :class:`KPI` objects with computation helpers."""

    def __init__(self) -> None:
        self._registry: dict[str, KPI] = {}

    def register(self, kpi: KPI) -> None:
        self._registry[kpi.id] = kpi

    def get(self, kpi_id: str) -> KPI:
        if kpi_id not in self._registry:
            raise KeyError(f"KPI '{kpi_id}' is not registered")
        return self._registry[kpi_id]

    def list_by_category(self, category: str) -> list[KPI]:
        return [k for k in self._registry.values() if k.category == category]

    def list_all(self) -> list[KPI]:
        return list(self._registry.values())

    def compute(
        self,
        kpi_id: str,
        treatment_df: pd.DataFrame,
        control_df: Optional[pd.DataFrame] = None,
    ) -> float:
        """Evaluate a KPI given *treatment_df* (and optionally *control_df*)."""
        kpi = self.get(kpi_id)
        return kpi.formula_func(treatment_df, control_df)


# ---------------------------------------------------------------------------
# KPI formula functions
# ---------------------------------------------------------------------------


def _net_revenue_uplift_pct(
    treatment: pd.DataFrame, control: Optional[pd.DataFrame]
) -> float:
    t_rev = treatment["net_sales"].sum()
    c_rev = (
        control["net_sales"].sum() if control is not None and len(control) else t_rev
    )
    if c_rev == 0:
        return 0.0
    return (t_rev - c_rev) / c_rev * 100


def _promo_roi_pct(treatment: pd.DataFrame, _control: Optional[pd.DataFrame]) -> float:
    promo = treatment[treatment["promo_flag"] == 1]
    if promo.empty:
        return 0.0
    gross = promo["units_sold"] * promo["list_price"]
    net = gross * (1 - promo["discount_pct"])
    cogs = promo["purchase_cost"] * promo["units_sold"]
    margin = (net - cogs).sum()
    promo_cost = (gross * promo["discount_pct"]).sum()
    if promo_cost == 0:
        return 0.0
    return margin / promo_cost * 100


def _gross_to_net_leakage_pct(
    treatment: pd.DataFrame, _control: Optional[pd.DataFrame]
) -> float:
    gross = treatment["gross_sales"].sum()
    net = treatment["net_sales"].sum()
    if gross == 0:
        return 0.0
    return (gross - net) / gross * 100


def _purchase_cost_reduction_pct(
    treatment: pd.DataFrame, control: Optional[pd.DataFrame]
) -> float:
    baseline = (
        control["purchase_cost"].mean()
        if control is not None and len(control)
        else treatment["purchase_cost"].mean()
    )
    realized = treatment["purchase_cost"].mean()
    if baseline == 0:
        return 0.0
    return (baseline - realized) / baseline * 100


def _supplier_lead_time_reliability_pct(
    treatment: pd.DataFrame, _control: Optional[pd.DataFrame]
) -> float:
    # Heuristic: on-time = lead_time_days <= median lead_time
    median_lt = treatment["lead_time_days"].median()
    on_time = (treatment["lead_time_days"] <= median_lt).sum()
    total = len(treatment)
    if total == 0:
        return 0.0
    return on_time / total * 100


def _negotiated_savings_realization_pct(
    treatment: pd.DataFrame, control: Optional[pd.DataFrame]
) -> float:
    baseline_cost = (
        control["purchase_cost"].mean()
        if control is not None and len(control)
        else treatment["purchase_cost"].mean()
    )
    realized_cost = treatment["purchase_cost"].mean()
    negotiated_savings = baseline_cost - realized_cost
    if baseline_cost == 0:
        return 0.0
    return negotiated_savings / baseline_cost * 100


def _contribution_margin_uplift_pct(
    treatment: pd.DataFrame, control: Optional[pd.DataFrame]
) -> float:
    def _cm(df: pd.DataFrame) -> float:
        return (df["net_sales"] - df["purchase_cost"] * df["units_sold"]).sum()

    t_cm = _cm(treatment)
    c_cm = _cm(control) if control is not None and len(control) else t_cm
    if c_cm == 0:
        return 0.0
    return (t_cm - c_cm) / abs(c_cm) * 100


def _pilot_payback_period_days(
    treatment: pd.DataFrame, control: Optional[pd.DataFrame]
) -> float:
    """Simplified payback: days of incremental margin to cover a notional pilot cost.

    Uses an assumed fixed pilot cost of 50 000 (currency units) — the real cost
    will come from the project configuration in later milestones.
    """
    pilot_cost = 50_000.0
    t_margin = (
        treatment["net_sales"] - treatment["purchase_cost"] * treatment["units_sold"]
    ).sum()
    c_margin = (
        (control["net_sales"] - control["purchase_cost"] * control["units_sold"]).sum()
        if control is not None and len(control)
        else 0.0
    )
    daily_incremental = t_margin - c_margin
    n_days = treatment["date"].nunique() or 1
    daily_rate = daily_incremental / n_days
    if daily_rate <= 0:
        return float("inf")
    return pilot_cost / daily_rate


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def default_kpi_catalog() -> KPICatalog:
    """Return a :class:`KPICatalog` pre-loaded with standard FMCG OS KPIs."""
    cat = KPICatalog()

    # Commercial KPIs
    cat.register(
        KPI(
            "net_revenue_uplift_pct",
            "Net Revenue Uplift %",
            "(treatment_net_revenue − control_expected_net_revenue) / control_expected_net_revenue × 100",
            _net_revenue_uplift_pct,
            "commercial",
            cadence="weekly",
            description="Percentage uplift in net revenue vs. control group.",
        )
    )
    cat.register(
        KPI(
            "promo_roi_pct",
            "Promo ROI %",
            "incremental_net_margin_from_promo / promo_cost × 100",
            _promo_roi_pct,
            "commercial",
            cadence="weekly",
            description="Return on promotional investment.",
        )
    )
    cat.register(
        KPI(
            "gross_to_net_leakage_pct",
            "Gross-to-Net Leakage %",
            "(gross_sales − net_sales) / gross_sales × 100",
            _gross_to_net_leakage_pct,
            "commercial",
            cadence="monthly",
            description="Revenue leakage between gross and net sales.",
        )
    )

    # Procurement KPIs
    cat.register(
        KPI(
            "purchase_cost_reduction_pct",
            "Purchase Cost Reduction %",
            "(baseline_unit_cost − realized_unit_cost) / baseline_unit_cost × 100",
            _purchase_cost_reduction_pct,
            "procurement",
            cadence="monthly",
            description="Reduction in average purchase cost vs. baseline.",
        )
    )
    cat.register(
        KPI(
            "supplier_lead_time_reliability_pct",
            "Supplier Lead-Time Reliability %",
            "on_time_deliveries / total_deliveries × 100",
            _supplier_lead_time_reliability_pct,
            "procurement",
            cadence="monthly",
            description="Percentage of deliveries within acceptable lead time.",
        )
    )
    cat.register(
        KPI(
            "negotiated_savings_realization_pct",
            "Negotiated Savings Realisation %",
            "realized_savings / negotiated_savings × 100",
            _negotiated_savings_realization_pct,
            "procurement",
            cadence="monthly",
            description="How much of the negotiated savings actually materialised.",
        )
    )

    # Shared KPIs
    cat.register(
        KPI(
            "contribution_margin_uplift_pct",
            "Contribution Margin Uplift %",
            "(treatment_CM − control_CM) / |control_CM| × 100",
            _contribution_margin_uplift_pct,
            "shared",
            cadence="monthly",
            description="Uplift in contribution margin vs. control.",
        )
    )
    cat.register(
        KPI(
            "pilot_payback_period_days",
            "Pilot Payback Period (days)",
            "pilot_cost / daily_incremental_margin",
            _pilot_payback_period_days,
            "shared",
            cadence="monthly",
            description="Estimated days until pilot investment is recovered.",
        )
    )

    return cat
