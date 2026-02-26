import json
import sqlite3
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_insights() -> dict:
    insights_path = PROJECT_ROOT / "procurement_insights.json"
    with open(insights_path, "r", encoding="utf-8") as file:
        return json.load(file)


def test_sql_total_spend_reconciles_with_insights_json():
    conn = sqlite3.connect(PROJECT_ROOT / "procurement.db")
    sql_total_spend = conn.execute("SELECT ROUND(SUM(total_amount_ngn), 0) FROM purchase_orders").fetchone()[0]
    conn.close()

    insights = _load_insights()
    assert float(sql_total_spend) == pytest.approx(float(insights["total_spend"]), abs=1.0)


def test_sql_maverick_spend_reconciles_with_insights_json():
    conn = sqlite3.connect(PROJECT_ROOT / "procurement.db")
    sql_maverick_spend = conn.execute(
        """
        SELECT ROUND(SUM(po.total_amount_ngn), 0)
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        WHERE s.is_approved = 0 OR s.risk_level = 'High'
        """
    ).fetchone()[0]
    conn.close()

    insights = _load_insights()
    assert float(sql_maverick_spend) == pytest.approx(float(insights["maverick_spend"]), abs=1.0)


def test_sql_price_standardization_reconciles_with_insights_json():
    conn = sqlite3.connect(PROJECT_ROOT / "procurement.db")
    sql_price_standardization = conn.execute(
        """
        SELECT COALESCE(SUM(potential_savings), 0)
        FROM (
            SELECT
                ROUND(SUM(total_amount_ngn) * (AVG(unit_price_ngn) - MIN(unit_price_ngn)) / AVG(unit_price_ngn), 0) AS potential_savings
            FROM purchase_orders
            GROUP BY material_name, category
            HAVING COUNT(DISTINCT supplier_id) > 1
               AND ROUND((AVG(unit_price_ngn) - MIN(unit_price_ngn)) / MIN(unit_price_ngn) * 100, 2) > 10
            ORDER BY potential_savings DESC
            LIMIT 10
        )
        """
    ).fetchone()[0]
    conn.close()

    insights = _load_insights()
    assert float(sql_price_standardization) == pytest.approx(
        float(insights["price_standardization_savings"]),
        abs=2.0,
    )