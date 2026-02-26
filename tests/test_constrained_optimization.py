import sqlite3

from constrained_optimization import run_constrained_optimization


def _build_test_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE suppliers (
            supplier_id TEXT,
            supplier_name TEXT,
            category TEXT,
            country TEXT,
            payment_terms TEXT,
            currency TEXT,
            quality_rating REAL,
            is_approved INTEGER,
            risk_level TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE purchase_orders (
            po_number TEXT,
            po_date TEXT,
            supplier_id TEXT,
            supplier_name TEXT,
            material_id TEXT,
            material_name TEXT,
            category TEXT,
            quantity REAL,
            unit_price_ngn REAL,
            total_amount_ngn REAL,
            total_amount_usd REAL,
            currency TEXT,
            expected_delivery_date TEXT,
            actual_delivery_date TEXT,
            delivery_status TEXT,
            payment_status TEXT,
            buyer TEXT,
            plant_location TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE quality_incidents (
            incident_id TEXT,
            po_number TEXT,
            supplier_id TEXT,
            incident_type TEXT,
            severity TEXT,
            cost_impact_ngn REAL
        )
        """
    )

    suppliers = [
        ("SUP1", "Supplier A", "Packaging", "NG", "Net 30", "NGN", 4.7, 1, "Low"),
        ("SUP2", "Supplier B", "Packaging", "NG", "Net 30", "NGN", 4.2, 1, "Medium"),
        ("SUP3", "Supplier C", "Packaging", "NG", "Net 30", "NGN", 3.8, 1, "High"),
    ]

    purchase_orders = [
        ("PO1", "2025-01-01", "SUP1", "Supplier A", "M1", "Bottle", "Packaging", 100, 10, 1000, None, "NGN", "2025-01-10", "2025-01-09", "Delivered", "Paid", "Buyer", "Lagos"),
        ("PO2", "2025-01-02", "SUP2", "Supplier B", "M1", "Bottle", "Packaging", 120, 11, 1320, None, "NGN", "2025-01-11", "2025-01-11", "Delivered", "Paid", "Buyer", "Lagos"),
        ("PO3", "2025-01-03", "SUP3", "Supplier C", "M1", "Bottle", "Packaging", 130, 13, 1690, None, "NGN", "2025-01-12", "2025-01-15", "Delivered", "Paid", "Buyer", "Lagos"),
        ("PO4", "2025-01-04", "SUP1", "Supplier A", "M2", "Cap", "Packaging", 140, 9, 1260, None, "NGN", "2025-01-13", "2025-01-12", "Delivered", "Paid", "Buyer", "Lagos"),
    ]

    incidents = [
        ("QI1", "PO3", "SUP3", "Defect", "High", 100.0),
    ]

    cur.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", suppliers)
    cur.executemany("INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", purchase_orders)
    cur.executemany("INSERT INTO quality_incidents VALUES (?, ?, ?, ?, ?, ?)", incidents)

    conn.commit()
    return conn


def test_constrained_optimization_returns_rows_and_summary():
    conn = _build_test_conn()

    constraints = {
        "min_on_time_delivery_pct": 80.0,
        "max_quality_incidents_per_order": 2.0,
        "max_risk_level": "Medium",
        "min_dual_source_threshold": 1000.0,
        "min_price_percentile": 0.30,
        "max_single_supplier_share": 0.80,
    }

    recs, summary = run_constrained_optimization(conn=conn, constraints=constraints)

    assert not recs.empty
    assert {"category", "supplier_id", "constrained_share", "projected_spend_ngn"}.issubset(set(recs.columns))
    assert summary["constrained_spend_ngn"] > 0
    assert summary["constrained_savings_ngn"] >= 0
    assert summary["constrained_savings_pct"] >= 0

    conn.close()


def test_constrained_optimization_dual_source_summary_key_present():
    conn = _build_test_conn()

    constraints = {
        "min_on_time_delivery_pct": 0.0,
        "max_quality_incidents_per_order": 10.0,
        "max_risk_level": "High",
        "min_dual_source_threshold": 1.0,
        "min_price_percentile": 0.0,
        "max_single_supplier_share": 0.80,
    }

    _, summary = run_constrained_optimization(conn=conn, constraints=constraints)
    assert "dual_sourced_categories" in summary
    assert isinstance(summary["dual_sourced_categories"], int)

    conn.close()
