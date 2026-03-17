"""Supplier allocation optimization using mathematical programming."""

from __future__ import annotations

import sqlite3
from typing import Dict, Tuple

import pandas as pd

from procurement_spend_analysis.optimization import optimize_supplier_mix


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

    result = optimize_supplier_mix(
        supplier_metrics=supplier_metrics,
        category_history=category_history,
        max_suppliers_per_category=max_suppliers_per_category,
        min_supplier_share=min_supplier_share,
        max_single_supplier_share=1.0,
        score_weights=score_weights,
    )

    recommendations_df = result.recommendations.copy()
    if not recommendations_df.empty and "composite_penalty" in recommendations_df.columns:
        recommendations_df["composite_score"] = 1 - recommendations_df["composite_penalty"]
    return recommendations_df, result.summary
