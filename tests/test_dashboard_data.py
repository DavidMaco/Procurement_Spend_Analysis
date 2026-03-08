import io
import zipfile

import pandas as pd
import pytest

from dashboard_data import (
    MAX_UPLOAD_FILE_SIZE_MB,
    MAX_UPLOAD_ROWS_PER_FILE,
    UploadValidationError,
    _grade_supplier_performance,
    _validate_upload_size,
    build_bundle_from_upload_bytes,
    build_bundle_from_uploaded_frames,
    export_powerbi_pack,
    export_upload_template_pack,
    generate_demo_bundle,
    infer_dataset_key,
    normalize_raw_tables,
    prepare_dashboard_context,
)


def test_generate_demo_bundle_produces_expected_tables():
    bundle = generate_demo_bundle(num_orders=250, seed=7, num_quality_incidents=30)

    assert bundle["metadata"]["source_label"] == "Generated realistic demo dataset"
    assert bundle["raw"]["purchase_orders"].shape[0] == 250
    assert "procurement_insights_summary" in bundle["analytics"]
    assert bundle["insights"]["total_spend"] > 0


def test_external_upload_normalization_accepts_alias_columns():
    suppliers = pd.DataFrame(
        {
            "vendor_id": ["SUP1"],
            "vendor_name": ["Acme Supplies"],
            "supplier_category": ["Packaging"],
            "country_name": ["Nigeria"],
        }
    )
    materials = pd.DataFrame(
        {
            "item_code": ["MAT1"],
            "item_name": ["Bottle"],
            "material_category": ["Packaging"],
            "std_price": [1250],
        }
    )
    purchase_orders = pd.DataFrame(
        {
            "purchase_order_number": ["PO1"],
            "order_date": ["2025-01-01"],
            "vendor_id": ["SUP1"],
            "item_code": ["MAT1"],
            "qty": [100],
            "unit_price": [1300],
            "invoice_currency": ["NGN"],
        }
    )

    normalized, rename_maps = normalize_raw_tables(
        {
            "suppliers": suppliers,
            "materials": materials,
            "purchase_orders": purchase_orders,
        }
    )

    assert normalized["purchase_orders"].loc[0, "total_amount_ngn"] == 130000
    assert normalized["purchase_orders"].loc[0, "supplier_name"] == "Acme Supplies"
    assert rename_maps["suppliers"]["vendor_id"] == "supplier_id"


def test_build_bundle_from_uploaded_frames_and_export_pack():
    suppliers = pd.DataFrame(
        {
            "supplier_id": ["SUP1"],
            "supplier_name": ["Acme Supplies"],
            "category": ["Packaging"],
            "country": ["Nigeria"],
            "payment_terms": ["Net 30"],
            "currency": ["NGN"],
            "quality_rating": [4.2],
            "is_approved": [True],
            "risk_level": ["Low"],
        }
    )
    materials = pd.DataFrame(
        {
            "material_id": ["MAT1"],
            "material_name": ["Bottle"],
            "category": ["Packaging"],
            "unit_of_measure": ["PCS"],
            "standard_price_ngn": [1200],
            "lead_time_days": [14],
        }
    )
    purchase_orders = pd.DataFrame(
        {
            "po_number": ["PO1", "PO2"],
            "po_date": ["2025-01-01", "2025-01-05"],
            "supplier_id": ["SUP1", "SUP1"],
            "material_id": ["MAT1", "MAT1"],
            "quantity": [100, 80],
            "unit_price_ngn": [1250, 1230],
            "currency": ["NGN", "NGN"],
            "delivery_status": ["Delivered", "Delivered"],
            "payment_status": ["Paid", "Paid"],
        }
    )
    quality = pd.DataFrame(
        {
            "po_number": ["PO1"],
            "cost_impact_ngn": [5000],
        }
    )

    bundle = build_bundle_from_uploaded_frames(
        {
            "suppliers": suppliers,
            "materials": materials,
            "purchase_orders": purchase_orders,
            "quality_incidents": quality,
        }
    )

    payload = export_powerbi_pack(bundle)

    assert bundle["metadata"]["quality_report"]["row_counts"]["purchase_orders"] == 2
    assert bundle["analytics"]["procurement_insights_summary"].shape[0] >= 10

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert "exports/procurement_insights_summary.csv" in names
        assert "powerbi/POWERBI_DEPLOYMENT_GUIDE.md" in names
        assert "powerbi/POWERBI_PBIT_STARTER_SPEC.json" in names


def test_prepare_dashboard_context_applies_category_filter():
    bundle = generate_demo_bundle(num_orders=300, seed=11, num_quality_incidents=35)
    context = prepare_dashboard_context(bundle, selected_categories=["Packaging"])

    assert context["filtered_pos"]["category"].nunique() == 1
    assert context["filtered_pos"]["category"].iloc[0] == "Packaging"
    assert context["metrics"]["filtered_total_spend"] > 0


def test_export_upload_template_pack_contains_expected_files():
    payload = export_upload_template_pack()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert "company_upload_templates/suppliers_template.csv" in names
        assert "company_upload_templates/materials_template.csv" in names
        assert "company_upload_templates/purchase_orders_template.csv" in names
        assert "company_upload_templates/quality_incidents_template.csv" in names


# ── error-path and edge-case tests ──────────────────────────────────────


def test_normalize_raw_tables_raises_when_required_dataset_missing():
    """Normalization must raise when a required dataset is absent."""
    with pytest.raises(UploadValidationError, match="Missing required dataset"):
        normalize_raw_tables({"suppliers": pd.DataFrame({"supplier_id": ["S1"], "supplier_name": ["A"]})})


def test_normalize_raw_tables_raises_when_required_column_missing():
    """Normalization must raise when a required column is absent after alias search."""
    with pytest.raises(UploadValidationError, match="missing required columns"):
        normalize_raw_tables({
            "suppliers": pd.DataFrame({"supplier_id": ["S1"], "supplier_name": ["A"]}),
            "materials": pd.DataFrame({"material_id": ["M1"], "material_name": ["B"]}),
            "purchase_orders": pd.DataFrame({
                "po_number": ["PO1"],
                "po_date": ["2025-01-01"],
                # supplier_id is missing — must trigger error
                "material_id": ["M1"],
                "quantity": [10],
            }),
        })


def test_build_bundle_from_upload_bytes_rejects_empty_upload():
    """An empty upload payload must raise UploadValidationError."""
    with pytest.raises(UploadValidationError, match="No supported CSV"):
        build_bundle_from_upload_bytes({"random_name.csv": b"a,b\n1,2\n"})


def test_validate_upload_size_rejects_oversized_file():
    """Files exceeding MAX_UPLOAD_FILE_SIZE_MB must be rejected."""
    fake_payload = b"x" * (MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024 + 1)
    with pytest.raises(UploadValidationError, match="exceeds"):
        _validate_upload_size(fake_payload, "huge_file.csv")


def test_grade_supplier_performance_returns_expected_grades():
    """Validate the A–E grading logic for several known scenarios."""
    grade_a = _grade_supplier_performance(pd.Series({"on_time_delivery_pct": 98, "quality_incidents": 0}))
    grade_c = _grade_supplier_performance(pd.Series({"on_time_delivery_pct": 85, "quality_incidents": 3}))
    grade_e = _grade_supplier_performance(pd.Series({"on_time_delivery_pct": 50, "quality_incidents": 10}))
    assert grade_a == "A"
    assert grade_c == "C"
    assert grade_e == "E"


def test_infer_dataset_key_from_diverse_filenames():
    """Filename-to-key inference must handle common ERP export names."""
    assert infer_dataset_key("vendor_master_extract.csv") == "suppliers"
    assert infer_dataset_key("PO_LINES_2025.csv") == "purchase_orders"
    assert infer_dataset_key("item_master.csv") == "materials"
    assert infer_dataset_key("non_conformance_log.csv") == "quality_incidents"
    assert infer_dataset_key("accounts_receivable.csv") is None


def test_normalize_handles_empty_quality_incidents_gracefully():
    """A bundle with no quality incidents should still normalize cleanly."""
    suppliers = pd.DataFrame({
        "supplier_id": ["S1"], "supplier_name": ["Test Supplier"],
        "category": ["Raw Materials"], "country": ["Nigeria"],
    })
    materials = pd.DataFrame({
        "material_id": ["M1"], "material_name": ["Test Item"],
        "category": ["Raw Materials"],
    })
    purchase_orders = pd.DataFrame({
        "po_number": ["PO1"], "po_date": ["2025-06-01"],
        "supplier_id": ["S1"], "material_id": ["M1"],
        "quantity": [50], "unit_price_ngn": [1000],
    })
    normalized, _ = normalize_raw_tables({
        "suppliers": suppliers,
        "materials": materials,
        "purchase_orders": purchase_orders,
        # quality_incidents intentionally omitted
    })
    assert "quality_incidents" in normalized
    assert normalized["quality_incidents"].empty or len(normalized["quality_incidents"]) == 0
