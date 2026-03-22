import pandas as pd
import pytest

from procurement_spend_analysis.security import sanitize_filename, validate_text_payload
from procurement_spend_analysis.validation import validate_canonical_tables


def test_validate_canonical_tables_accepts_valid_minimal_tables():
    tables = {
        "suppliers": pd.DataFrame(
            [
                {
                    "supplier_id": "SUP1",
                    "supplier_name": "Supplier A",
                    "category": "Packaging",
                    "country": "Nigeria",
                    "payment_terms": "Net 30",
                    "currency": "NGN",
                    "quality_rating": 4.2,
                    "is_approved": True,
                    "risk_level": "Low",
                }
            ]
        ),
        "materials": pd.DataFrame(
            [
                {
                    "material_id": "MAT1",
                    "material_name": "Bottle",
                    "category": "Packaging",
                    "unit_of_measure": "PCS",
                    "standard_price_ngn": 1200.0,
                    "lead_time_days": 14,
                }
            ]
        ),
        "purchase_orders": pd.DataFrame(
            [
                {
                    "po_number": "PO1",
                    "po_date": pd.Timestamp("2025-01-01"),
                    "supplier_id": "SUP1",
                    "supplier_name": "Supplier A",
                    "material_id": "MAT1",
                    "material_name": "Bottle",
                    "category": "Packaging",
                    "quantity": 100.0,
                    "unit_price_ngn": 1200.0,
                    "total_amount_ngn": 120000.0,
                    "total_amount_usd": None,
                    "currency": "NGN",
                    "expected_delivery_date": pd.Timestamp("2025-01-10"),
                    "actual_delivery_date": pd.Timestamp("2025-01-09"),
                    "delivery_status": "Delivered",
                    "payment_status": "Paid",
                    "buyer": "Buyer",
                    "plant_location": "Lagos",
                }
            ]
        ),
        "quality_incidents": pd.DataFrame(
            [
                {
                    "incident_id": "QI1",
                    "po_number": "PO1",
                    "supplier_id": "SUP1",
                    "incident_type": "Defect",
                    "severity": "High",
                    "cost_impact_ngn": 2500.0,
                }
            ]
        ),
    }

    validated = validate_canonical_tables(tables)
    assert set(validated) == {
        "suppliers",
        "materials",
        "purchase_orders",
        "quality_incidents",
    }


def test_sanitize_filename_rejects_path_traversal_and_non_csv():
    with pytest.raises(ValueError):
        sanitize_filename("../suppliers.csv")
    with pytest.raises(ValueError):
        sanitize_filename("suppliers.xlsx")


def test_validate_text_payload_rejects_null_bytes():
    with pytest.raises(ValueError):
        validate_text_payload("bad\x00payload")
