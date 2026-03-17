"""Semantic metrics layer for FMCG revenue and procurement analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import pandas as pd


@dataclass(frozen=True)
class Metric:
    """Declarative metric definition."""

    name: str
    formula: Callable[[pd.DataFrame], pd.Series]
    dimensions: list[str] = field(default_factory=list)
    grain: str = "sku_store_day"
    description: str = ""


class SemanticMetricsLayer:
    """Registry that holds :class:`Metric` objects and evaluates them on DataFrames."""

    def __init__(self) -> None:
        self._registry: dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        self._registry[metric.name] = metric

    def get_metric(self, name: str) -> Metric:
        if name not in self._registry:
            raise KeyError(f"Metric '{name}' is not registered")
        return self._registry[name]

    def list_metrics(self) -> list[Metric]:
        return list(self._registry.values())

    def compute(
        self,
        metric_name: str,
        df: pd.DataFrame,
        group_by: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Evaluate a metric on *df*, optionally aggregating by *group_by* columns.

        When *group_by* is ``None`` the raw per-row metric column is returned.
        When *group_by* is provided the metric is summed within each group.
        """
        metric = self.get_metric(metric_name)
        result = metric.formula(df)
        out = df.copy()
        out[metric_name] = result

        if group_by:
            return out.groupby(group_by, as_index=False)[[metric_name]].sum()
        return out[[metric_name]]


# ---------------------------------------------------------------------------
# Pre-registered metrics
# ---------------------------------------------------------------------------

def _gross_sales(df: pd.DataFrame) -> pd.Series:
    return df["units_sold"] * df["list_price"]


def _net_sales(df: pd.DataFrame) -> pd.Series:
    return _gross_sales(df) * (1 - df["discount_pct"])


def _promo_roi(df: pd.DataFrame) -> pd.Series:
    """Simplified promo ROI: per-row ratio of incremental net sales to discount amount.

    For promo rows (promo_flag=1) the discount_amount is the denominator.
    Non-promo rows return NaN because the concept is undefined.
    """
    gross = _gross_sales(df)
    net = gross * (1 - df["discount_pct"])
    discount_amount = gross * df["discount_pct"]

    # Baseline is full-price net (discount_pct=0 equivalent) → gross itself
    incremental = net - gross  # always <= 0 per row; aggregate comparison is external
    # Avoid division by zero
    roi = incremental / discount_amount.replace(0, float("nan"))
    # Mark non-promo rows as NaN
    roi = roi.where(df["promo_flag"] == 1, other=float("nan"))
    return roi


def _gross_to_net_leakage(df: pd.DataFrame) -> pd.Series:
    gross = _gross_sales(df)
    net = _net_sales(df)
    return (gross - net) / gross.replace(0, float("nan"))


def _unit_margin(df: pd.DataFrame) -> pd.Series:
    net = _net_sales(df)
    units = df["units_sold"].replace(0, float("nan"))
    return (net / units) - df["purchase_cost"]


def _purchase_cost_total(df: pd.DataFrame) -> pd.Series:
    return df["purchase_cost"] * df["units_sold"]


def _contribution_margin(df: pd.DataFrame) -> pd.Series:
    return _net_sales(df) - (df["purchase_cost"] * df["units_sold"])


def default_metrics_layer() -> SemanticMetricsLayer:
    """Factory returning a :class:`SemanticMetricsLayer` with all standard FMCG metrics."""
    layer = SemanticMetricsLayer()
    layer.register(Metric(
        name="gross_sales",
        formula=_gross_sales,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="units_sold × list_price",
    ))
    layer.register(Metric(
        name="net_sales",
        formula=_net_sales,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="gross_sales × (1 − discount_pct)",
    ))
    layer.register(Metric(
        name="promo_roi",
        formula=_promo_roi,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="Incremental net margin from promo rows / discount amount",
    ))
    layer.register(Metric(
        name="gross_to_net_leakage",
        formula=_gross_to_net_leakage,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="(gross_sales − net_sales) / gross_sales",
    ))
    layer.register(Metric(
        name="unit_margin",
        formula=_unit_margin,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="(net_sales / units_sold) − purchase_cost",
    ))
    layer.register(Metric(
        name="purchase_cost_total",
        formula=_purchase_cost_total,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="purchase_cost × units_sold",
    ))
    layer.register(Metric(
        name="contribution_margin",
        formula=_contribution_margin,
        dimensions=["sku_id", "store_id", "date"],
        grain="sku_store_day",
        description="net_sales − (purchase_cost × units_sold)",
    ))
    return layer
