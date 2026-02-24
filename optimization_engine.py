"""
Supplier allocation optimization engine.
Builds score-based supplier recommendations by category and estimates savings.
"""

from __future__ import annotations

import sqlite3
from typing import Dict, Tuple

import pandas as pd


RISK_SCORES = {
    "Low": 1.0,
    "Medium": 0.6,
    "High": 0.2,
}


def _minmax(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    min_val = series.min()
    max_val = series.max()
    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series([1.0] * len(series), index=series.index)
    scaled = (series - min_val) / (max_val - min_val)
    return scaled if higher_is_better else (1 - scaled)


def _allocate_shares(scores: pd.Series, min_share: float) -> pd.Series:
    if len(scores) == 0:
        return pd.Series(dtype=float)

    base = scores / scores.sum() if scores.sum() > 0 else pd.Series([1.0 / len(scores)] * len(scores), index=scores.index)
    adjusted = base.clip(lower=min_share)
    adjusted = adjusted / adjusted.sum()
    return adjusted


def run_supplier_optimization(
    conn: sqlite3.Connection,
    max_suppliers_per_category: int = 3,
    min_supplier_share: float = 0.15,
    score_weights: Dict[str, float] | None = None,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Generate supplier recommendations and summarize expected savings."""

    if score_weights is None:
        score_weights = {
            "unit_cost": 0.45,
            "delivery": 0.30,
            "quality": 0.15,
            "risk": 0.10,
        }

    supplier_metrics = pd.read_sql(
        """
        SELECT
            po.category,
            po.supplier_id,
            po.supplier_name,
            ROUND(SUM(po.quantity), 2) AS total_quantity,
            ROUND(SUM(po.total_amount_ngn), 2) AS total_spend_ngn,
            ROUND(SUM(po.total_amount_ngn) / NULLIF(SUM(po.quantity), 0), 4) AS avg_unit_cost_ngn,
            ROUND(
              SUM(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 ELSE 0 END) * 100.0 /
              NULLIF(COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END), 0),
              2
            ) AS on_time_delivery_pct,
            ROUND(COALESCE(SUM(qi.cost_impact_ngn), 0), 2) AS quality_cost_ngn,
            s.risk_level
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        LEFT JOIN quality_incidents qi ON po.po_number = qi.po_number
        GROUP BY po.category, po.supplier_id, po.supplier_name, s.risk_level
        HAVING total_quantity > 0
        """,
        conn,
    )

    category_history = pd.read_sql(
        """
        SELECT
            category,
            ROUND(SUM(quantity), 2) AS category_quantity,
            ROUND(SUM(total_amount_ngn), 2) AS category_spend_ngn,
            ROUND(SUM(total_amount_ngn) / NULLIF(SUM(quantity), 0), 4) AS category_avg_unit_cost
        FROM purchase_orders
        GROUP BY category
        """,
        conn,
    )

    if supplier_metrics.empty:
        return pd.DataFrame(), {
            "optimized_spend_ngn": 0.0,
            "historical_spend_ngn": 0.0,
            "optimization_savings_ngn": 0.0,
            "optimization_savings_pct": 0.0,
        }

    recommendations = []

    for category, frame in supplier_metrics.groupby("category"):
        group = frame.copy()

        group["cost_score"] = _minmax(group["avg_unit_cost_ngn"], higher_is_better=False)
        group["delivery_score"] = _minmax(group["on_time_delivery_pct"], higher_is_better=True)
        group["quality_score"] = _minmax(group["quality_cost_ngn"], higher_is_better=False)
        group["risk_score"] = group["risk_level"].map(RISK_SCORES).fillna(0.4)

        group["composite_score"] = (
            score_weights["unit_cost"] * group["cost_score"]
            + score_weights["delivery"] * group["delivery_score"]
            + score_weights["quality"] * group["quality_score"]
            + score_weights["risk"] * group["risk_score"]
        )

        selected = group.sort_values("composite_score", ascending=False).head(max_suppliers_per_category).copy()
        selected["recommended_share"] = _allocate_shares(selected["composite_score"], min_supplier_share)

        history_row = category_history[category_history["category"] == category].iloc[0]
        selected["projected_quantity"] = selected["recommended_share"] * history_row["category_quantity"]
        selected["projected_spend_ngn"] = selected["projected_quantity"] * selected["avg_unit_cost_ngn"]

        selected["historical_category_spend_ngn"] = history_row["category_spend_ngn"]
        selected["historical_category_avg_unit_cost"] = history_row["category_avg_unit_cost"]

        recommendations.append(selected)

    recommendations_df = pd.concat(recommendations, ignore_index=True)

    projected_by_category = (
        recommendations_df.groupby("category", as_index=False)["projected_spend_ngn"].sum()
        .rename(columns={"projected_spend_ngn": "optimized_category_spend_ngn"})
    )

    comparison = category_history.merge(projected_by_category, on="category", how="left")
    comparison["optimized_category_spend_ngn"] = comparison["optimized_category_spend_ngn"].fillna(comparison["category_spend_ngn"])

    historical_spend = float(comparison["category_spend_ngn"].sum())
    optimized_spend = float(comparison["optimized_category_spend_ngn"].sum())
    savings = max(0.0, historical_spend - optimized_spend)
    savings_pct = (savings / historical_spend * 100) if historical_spend > 0 else 0.0

    summary = {
        "historical_spend_ngn": historical_spend,
        "optimized_spend_ngn": optimized_spend,
        "optimization_savings_ngn": savings,
        "optimization_savings_pct": savings_pct,
    }

    return recommendations_df, summary
