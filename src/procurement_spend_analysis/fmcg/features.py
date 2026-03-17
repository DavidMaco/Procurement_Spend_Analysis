"""Feature store for FMCG demand-driver engineering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Feature:
    """Declarative feature definition."""

    name: str
    source_columns: list[str] = field(default_factory=list)
    transform: Callable[[pd.DataFrame], pd.Series] = field(default=lambda df: pd.Series(dtype="object"))
    description: str = ""


class FeatureStore:
    """Registry that holds :class:`Feature` objects and materialises them onto a DataFrame."""

    def __init__(self) -> None:
        self._registry: dict[str, Feature] = {}

    def register(self, feature: Feature) -> None:
        self._registry[feature.name] = feature

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply every registered transform and return *df* augmented with new columns."""
        out = df.copy()
        for feat in self._registry.values():
            out[feat.name] = feat.transform(out)
        return out

    def list_features(self) -> list[Feature]:
        return list(self._registry.values())


# ---------------------------------------------------------------------------
# Pre-registered feature transforms
# ---------------------------------------------------------------------------

def _is_promo(df: pd.DataFrame) -> pd.Series:
    return df["promo_flag"].astype(int)


def _discount_depth(df: pd.DataFrame) -> pd.Series:
    conditions = [
        df["discount_pct"] == 0,
        df["discount_pct"] <= 0.1,
        df["discount_pct"] <= 0.2,
        df["discount_pct"] <= 0.3,
    ]
    choices = ["0", "0-0.1", "0.1-0.2", "0.2-0.3"]
    return pd.Series(np.select(conditions, choices, default="0.3+"), index=df.index)


def _day_type(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.where(
            df["is_holiday"] == 1,
            "holiday",
            np.where(df["is_weekend"] == 1, "weekend", "weekday"),
        ),
        index=df.index,
    )


def _temp_bucket(df: pd.DataFrame) -> pd.Series:
    conditions = [
        df["temperature"] < 10,
        df["temperature"] < 20,
        df["temperature"] < 30,
    ]
    choices = ["cold", "mild", "warm"]
    return pd.Series(np.select(conditions, choices, default="hot"), index=df.index)


def _rain_flag(df: pd.DataFrame) -> pd.Series:
    return (df["rain_mm"] > 0).astype(int)


def _stock_risk(df: pd.DataFrame) -> pd.Series:
    conditions = [
        df["stock_out_flag"] == 1,
        df["stock_on_hand"] < 50,
        df["stock_on_hand"] < 200,
    ]
    choices = ["stockout", "low", "adequate"]
    return pd.Series(np.select(conditions, choices, default="high"), index=df.index)


def _lead_time_bucket(df: pd.DataFrame) -> pd.Series:
    conditions = [
        df["lead_time_days"] <= 5,
        df["lead_time_days"] <= 10,
    ]
    choices = ["short", "medium"]
    return pd.Series(np.select(conditions, choices, default="long"), index=df.index)


def _price_tier(df: pd.DataFrame) -> pd.Series:
    """Quartile-based price tier within each category."""
    def _quartile_label(s: pd.Series) -> pd.Series:
        try:
            return pd.qcut(s, q=4, labels=["Q1_budget", "Q2_value", "Q3_premium", "Q4_luxury"], duplicates="drop")
        except ValueError:
            # Fewer than 4 distinct values → assign a single tier
            return pd.Series("Q1_budget", index=s.index)

    return df.groupby("category")["list_price"].transform(_quartile_label)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def default_feature_store() -> FeatureStore:
    """Return a :class:`FeatureStore` pre-loaded with standard FMCG demand-driver features."""
    store = FeatureStore()
    store.register(Feature("is_promo", ["promo_flag"], _is_promo, "Binary promo indicator"))
    store.register(Feature("discount_depth", ["discount_pct"], _discount_depth, "Bucketed discount depth"))
    store.register(Feature("day_type", ["is_weekend", "is_holiday"], _day_type, "weekday / weekend / holiday"))
    store.register(Feature("temp_bucket", ["temperature"], _temp_bucket, "Temperature bucket: cold/mild/warm/hot"))
    store.register(Feature("rain_flag", ["rain_mm"], _rain_flag, "Binary: rained on that day"))
    store.register(Feature("stock_risk", ["stock_out_flag", "stock_on_hand"], _stock_risk, "Inventory risk level"))
    store.register(Feature("lead_time_bucket", ["lead_time_days"], _lead_time_bucket, "Lead-time bucket: short/medium/long"))
    store.register(Feature("price_tier", ["list_price", "category"], _price_tier, "Price quartile within category"))
    return store
