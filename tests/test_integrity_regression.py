import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_procurement_db_core_tables_have_rows():
    db_path = PROJECT_ROOT / "procurement.db"
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for table_name in ["suppliers", "materials", "purchase_orders", "quality_incidents"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        assert count > 0

    conn.close()


def test_insights_json_contains_regression_guardrails():
    insights_path = PROJECT_ROOT / "procurement_insights.json"
    assert insights_path.exists()

    with open(insights_path, "r", encoding="utf-8") as f:
        insights = json.load(f)

    required_numeric_keys = [
        "total_spend",
        "total_savings",
        "savings_percentage",
        "optimization_savings",
        "constrained_savings_ngn",
        "total_savings_p05_ngn",
        "total_savings_median_ngn",
        "total_savings_p95_ngn",
    ]

    for key in required_numeric_keys:
        assert key in insights
        assert isinstance(insights[key], (int, float))

    assert insights["total_spend"] > 0
    assert insights["total_savings"] >= 0
    assert 0 <= insights["savings_percentage"] <= 100
    assert insights["total_savings_p05_ngn"] <= insights["total_savings_median_ngn"] <= insights["total_savings_p95_ngn"]