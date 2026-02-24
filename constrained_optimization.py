"""
Constraint-optimized supplier allocation with service levels, risk caps, and dual-sourcing logic.
Uses a greedy scoring approach with hard constraints for SLA and risk thresholds.
"""

from __future__ import annotations

import sqlite3
from typing import Dict

import pandas as pd


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

    if supplier_metrics.empty:
        return pd.DataFrame(), {"constrained_spend_ngn": 0.0, "constrained_savings_ngn": 0.0}

    recommendations = []
    total_historical_spend = 0.0
    total_constrained_spend = 0.0

    risk_level_order = {"Low": 0, "Medium": 1, "High": 2}

    for category, frame in supplier_metrics.groupby("category"):
        group = frame.copy()
        group["risk_numeric"] = group["risk_level"].map(risk_level_order).fillna(3)

        otd_floor = float(constraints.get("min_on_time_delivery_pct", 0))
        quality_ceiling = float(constraints.get("max_quality_incidents_per_order", 5))
        max_risk = constraints.get("max_risk_level", "High")
        max_risk_numeric = risk_level_order.get(max_risk, 3)
        min_price_pct = float(constraints.get("min_price_percentile", 0.0))

        eligible = group[
            (group["on_time_delivery_pct"] >= otd_floor)
            & (group["quality_incident_count"] <= quality_ceiling)
            & (group["risk_numeric"] <= max_risk_numeric)
        ]

        if eligible.empty:
            eligible = group.nsmallest(1, "avg_unit_cost_ngn")

        if not eligible.empty:
            min_price = eligible["avg_unit_cost_ngn"].min()
            max_price = eligible["avg_unit_cost_ngn"].max()
            price_range = max_price - min_price if max_price > min_price else 1.0
            price_threshold = max_price - (1.0 - min_price_pct) * price_range

            price_qualified = eligible[eligible["avg_unit_cost_ngn"] <= price_threshold]

            if price_qualified.empty:
                price_qualified = eligible.nsmallest(1, "avg_unit_cost_ngn")

            max_single_share = float(constraints.get("max_single_supplier_share", 0.8))
            min_dual_source_threshold = float(constraints.get("min_dual_source_threshold", 0.5e11))

            history_row = category_history[category_history["category"] == category]
            if history_row.empty:
                continue

            category_spend = float(history_row["category_spend_ngn"].iloc[0])
            category_qty = float(history_row["category_quantity"].iloc[0])

            total_historical_spend += category_spend

            enforce_dual_source = category_spend > min_dual_source_threshold and len(price_qualified) > 1

            if enforce_dual_source:
                primary = price_qualified.nsmallest(1, "avg_unit_cost_ngn").iloc[0]
                primary_share = min(0.65, max_single_share)
                secondary_candidates = price_qualified[price_qualified["supplier_id"] != primary["supplier_id"]]
                if not secondary_candidates.empty:
                    secondary = secondary_candidates.nsmallest(1, "avg_unit_cost_ngn").iloc[0]
                    secondary_share = 1.0 - primary_share
                    for supp, share_val in [(primary, primary_share), (secondary, secondary_share)]:
                        rec = supp.copy()
                        rec["constrained_share"] = share_val
                        rec["projected_quantity"] = share_val * category_qty
                        rec["projected_spend_ngn"] = rec["projected_quantity"] * supp["avg_unit_cost_ngn"]
                        rec["historical_category_spend_ngn"] = category_spend
                        rec["dual_sourced"] = 1
                        recommendations.append(rec)
                        total_constrained_spend += float(rec["projected_spend_ngn"])
                else:
                    primary_rec = primary.copy()
                    primary_rec["constrained_share"] = 1.0
                    primary_rec["projected_quantity"] = category_qty
                    primary_rec["projected_spend_ngn"] = category_qty * primary["avg_unit_cost_ngn"]
                    primary_rec["historical_category_spend_ngn"] = category_spend
                    primary_rec["dual_sourced"] = 0
                    recommendations.append(primary_rec)
                    total_constrained_spend += float(primary_rec["projected_spend_ngn"])
            else:
                primary = price_qualified.nsmallest(1, "avg_unit_cost_ngn").iloc[0]
                primary_rec = primary.copy()
                primary_rec["constrained_share"] = 1.0
                primary_rec["projected_quantity"] = category_qty
                primary_rec["projected_spend_ngn"] = category_qty * primary["avg_unit_cost_ngn"]
                primary_rec["historical_category_spend_ngn"] = category_spend
                primary_rec["dual_sourced"] = 0
                recommendations.append(primary_rec)
                total_constrained_spend += float(primary_rec["projected_spend_ngn"])

    recommendations_df = pd.DataFrame(recommendations)

    constrained_savings = max(0.0, total_historical_spend - total_constrained_spend)
    constrained_savings_pct = (constrained_savings / total_historical_spend * 100) if total_historical_spend > 0 else 0.0

    summary = {
        "constrained_spend_ngn": float(total_constrained_spend),
        "constrained_savings_ngn": constrained_savings,
        "constrained_savings_pct": constrained_savings_pct,
        "dual_sourced_categories": int(recommendations_df["dual_sourced"].sum()),
    }

    return recommendations_df, summary
