import sqlite3

from optimization_engine import run_supplier_optimization


def test_run_supplier_optimization_returns_summary_and_rows():
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

    suppliers_rows = [
        ("SUP1", "Supplier A", "Packaging", "Nigeria", "Net 30", "NGN", 4.5, 1, "Low"),
        ("SUP2", "Supplier B", "Packaging", "Nigeria", "Net 30", "NGN", 4.0, 1, "Medium"),
        ("SUP3", "Supplier C", "Packaging", "Nigeria", "Net 30", "NGN", 3.8, 1, "High"),
    ]

    po_rows = [
        ("PO1", "2025-01-01", "SUP1", "Supplier A", "MAT1", "Bottle", "Packaging", 100, 10, 1000, None, "NGN", "2025-01-10", "2025-01-09", "Delivered", "Paid", "Buyer", "Lagos"),
        ("PO2", "2025-01-01", "SUP2", "Supplier B", "MAT1", "Bottle", "Packaging", 100, 12, 1200, None, "NGN", "2025-01-10", "2025-01-11", "Delivered", "Paid", "Buyer", "Lagos"),
        ("PO3", "2025-01-01", "SUP3", "Supplier C", "MAT1", "Bottle", "Packaging", 100, 15, 1500, None, "NGN", "2025-01-10", "2025-01-14", "Delivered", "Paid", "Buyer", "Lagos"),
    ]

    qi_rows = [
        ("QI1", "PO3", "SUP3", "Quality Defect", "High", 150),
    ]

    cur.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", suppliers_rows)
    cur.executemany("INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", po_rows)
    cur.executemany("INSERT INTO quality_incidents VALUES (?, ?, ?, ?, ?, ?)", qi_rows)

    conn.commit()

    recs, summary = run_supplier_optimization(conn, max_suppliers_per_category=2, min_supplier_share=0.2)

    assert not recs.empty
    assert {"category", "supplier_id", "recommended_share", "projected_spend_ngn"}.issubset(set(recs.columns))
    assert summary["historical_spend_ngn"] > 0
    assert summary["optimized_spend_ngn"] > 0
    assert summary["optimization_savings_ngn"] >= 0

    conn.close()
