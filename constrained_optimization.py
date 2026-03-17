"""Constraint-optimized supplier allocation using mathematical programming."""

from __future__ import annotations

import sqlite3
from typing import Dict

import pandas as pd

from procurement_spend_analysis.optimization import optimize_supplier_mix_with_constraints


def run_constrained_optimization(
    conn: sqlite3.Connection,
    constraints: Dict,
) -> tuple[pd.DataFrame, Dict[str, float]]:
    """
    Generate constrained supplier recommendations.

    Constraints dict keys:
    - max_single_supplier_share: [0, 1] cap on one supplier's category share
    - min_dual_source_threshold: [0, 1] if category spend > this, enforce dual sourcing
    - min_on_time_delivery_pct: OTD floor for supplier eligibility
    - max_quality_incidents_per_order: max incidents to still qualify
    - max_risk_level: acceptable risk level (Low/Medium/High)
    - min_price_percentile: accept suppliers at max price - (1 - percentile) * range
    """

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
            ROUND(COALESCE(COUNT(DISTINCT qi.incident_id), 0), 2) AS quality_incident_count,
            ROUND(COALESCE(SUM(qi.cost_impact_ngn), 0), 2) AS total_quality_cost_ngn,
            COUNT(DISTINCT po.po_number) AS total_orders,
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
            ROUND(SUM(total_amount_ngn), 2) AS category_spend_ngn
        FROM purchase_orders
        GROUP BY category
        """,
        conn,
    )

    result = optimize_supplier_mix_with_constraints(
        supplier_metrics=supplier_metrics,
        category_history=category_history,
        constraints=constraints,
    )
    return result.recommendations, result.summary
