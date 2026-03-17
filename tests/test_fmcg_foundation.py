"""Tests for FMCG OS Milestone 1 — models, metrics, features, reconciliation, KPIs, pilot."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.errors
import pytest

from procurement_spend_analysis.fmcg.features import default_feature_store
from procurement_spend_analysis.fmcg.kpi_catalog import default_kpi_catalog
from procurement_spend_analysis.fmcg.metrics import default_metrics_layer
from procurement_spend_analysis.fmcg.models import validate_fmcg_dataframe
from procurement_spend_analysis.fmcg.pilot import PilotConfig, select_pilot_cohort
from procurement_spend_analysis.fmcg.reconciliation import ReconciliationSuite, default_reconciliation_suite


# ---------------------------------------------------------------------------
# Shared fixture — ~100 realistic rows
# ---------------------------------------------------------------------------

def _make_row(
    idx: int,
    country: str,
    city: str,
    store: str,
    category: str,
    subcategory: str,
    brand: str,
    sku_id: str,
    sku_name: str,
    supplier: str,
    is_weekend: int,
    is_holiday: int,
    promo: int,
) -> dict:
    rng = np.random.RandomState(idx)
    units = rng.randint(1, 80)
    price = round(rng.uniform(2.0, 25.0), 2)
    discount = round(rng.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]), 2)
    gross = round(units * price, 2)
    net = round(gross * (1 - discount), 2)
    cost = round(rng.uniform(1.0, price * 0.8), 2)
    cogs = cost * units
    margin = round((net - cogs) / net, 3) if net > 0 else 0.0
    temp = round(rng.uniform(-5, 38), 2)
    rain = round(rng.uniform(0, 10), 2)
    stock = rng.randint(0, 500)
    stock_out = 1 if stock == 0 else 0
    lead = rng.randint(1, 20)
    day_offset = idx % 30
    date_str = f"1/{1 + day_offset}/2021"

    return {
        "date": date_str,
        "year": 2021,
        "month": 1,
        "day": 1 + day_offset,
        "weekofyear": 1 + (day_offset // 7),
        "weekday": day_offset % 7,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "temperature": temp,
        "rain_mm": rain,
        "store_id": store,
        "country": country,
        "city": city,
        "channel": "Hypermarket",
        "latitude": 52.52,
        "longitude": 13.39,
        "sku_id": sku_id,
        "sku_name": sku_name,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "units_sold": units,
        "list_price": price,
        "discount_pct": discount,
        "promo_flag": promo,
        "gross_sales": gross,
        "net_sales": net,
        "stock_on_hand": stock,
        "stock_out_flag": stock_out,
        "lead_time_days": lead,
        "supplier_id": supplier,
        "purchase_cost": cost,
        "margin_pct": margin,
    }


@pytest.fixture()
def sample_fmcg_df() -> pd.DataFrame:
    """~100-row DataFrame spanning 2 countries, 3 categories, 5 stores."""
    configs = [
        ("Germany", "Berlin", ["STORE001", "STORE002", "STORE003"]),
        ("France", "Paris", ["STORE004", "STORE005"]),
    ]
    categories = [
        ("Personal Care", "Shampoo", "BrandA", "SKU001", "BrandA Shampoo", "S001"),
        ("Beverages", "Juice", "BrandB", "SKU002", "BrandB Juice", "S002"),
        ("Snacks", "Chips", "BrandC", "SKU003", "BrandC Chips", "S003"),
    ]
    rows: list[dict] = []
    idx = 0
    for country, city, stores in configs:
        for store in stores:
            for cat, subcat, brand, sku, name, sup in categories:
                for _ in range(7):  # 7 rows per combo
                    is_wk = 1 if idx % 5 == 0 else 0
                    is_hol = 1 if idx % 20 == 0 else 0
                    promo = 1 if idx % 3 == 0 else 0
                    rows.append(_make_row(
                        idx, country, city, store, cat, subcat, brand,
                        sku, name, sup, is_wk, is_hol, promo,
                    ))
                    idx += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestFMCGSchema:
    def test_fmcg_schema_valid_data(self, sample_fmcg_df: pd.DataFrame) -> None:
        result = validate_fmcg_dataframe(sample_fmcg_df)
        assert len(result) == len(sample_fmcg_df)

    def test_fmcg_schema_rejects_invalid(self, sample_fmcg_df: pd.DataFrame) -> None:
        bad = sample_fmcg_df.copy()
        bad.loc[0, "units_sold"] = -5
        bad.loc[1, "discount_pct"] = 1.5
        bad.loc[2, "list_price"] = -1.0
        with pytest.raises(pandera.errors.SchemaErrors):
            validate_fmcg_dataframe(bad)


# ---------------------------------------------------------------------------
# Reconciliation tests
# ---------------------------------------------------------------------------

class TestReconciliation:
    def test_reconciliation_suite_passes_clean_data(self, sample_fmcg_df: pd.DataFrame) -> None:
        suite = default_reconciliation_suite()
        reports = suite.run(sample_fmcg_df)
        summary = ReconciliationSuite.summary(reports)
        for rule_name, info in summary.items():
            assert info["pass_rate"] == 1.0, f"{rule_name} failed on clean data"

    def test_reconciliation_suite_catches_gross_sales_mismatch(self, sample_fmcg_df: pd.DataFrame) -> None:
        bad = sample_fmcg_df.copy()
        bad.loc[0, "gross_sales"] = 0.0  # wrong
        suite = default_reconciliation_suite()
        reports = suite.run(bad)
        gross_report = next(r for r in reports if r.rule_name == "gross_sales_reconciliation")
        assert gross_report.failed_rows >= 1

    def test_reconciliation_suite_catches_net_sales_mismatch(self, sample_fmcg_df: pd.DataFrame) -> None:
        bad = sample_fmcg_df.copy()
        bad.loc[0, "net_sales"] = 0.0  # wrong
        suite = default_reconciliation_suite()
        reports = suite.run(bad)
        net_report = next(r for r in reports if r.rule_name == "net_sales_reconciliation")
        assert net_report.failed_rows >= 1


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_metrics_layer_compute_gross_sales(self, sample_fmcg_df: pd.DataFrame) -> None:
        layer = default_metrics_layer()
        result = layer.compute("gross_sales", sample_fmcg_df)
        expected = sample_fmcg_df["units_sold"] * sample_fmcg_df["list_price"]
        pd.testing.assert_series_equal(result["gross_sales"], expected, check_names=False)

    def test_metrics_layer_compute_gross_to_net_leakage(self, sample_fmcg_df: pd.DataFrame) -> None:
        layer = default_metrics_layer()
        result = layer.compute("gross_to_net_leakage", sample_fmcg_df)
        gross = sample_fmcg_df["units_sold"] * sample_fmcg_df["list_price"]
        net = gross * (1 - sample_fmcg_df["discount_pct"])
        expected = (gross - net) / gross
        pd.testing.assert_series_equal(
            result["gross_to_net_leakage"], expected, check_names=False, atol=1e-9,
        )


# ---------------------------------------------------------------------------
# Feature store tests
# ---------------------------------------------------------------------------

class TestFeatureStore:
    def test_feature_store_builds_all_features(self, sample_fmcg_df: pd.DataFrame) -> None:
        store = default_feature_store()
        built = store.build(sample_fmcg_df)
        for feat in store.list_features():
            assert feat.name in built.columns, f"Feature {feat.name} missing from output"
        assert len(built) == len(sample_fmcg_df)


# ---------------------------------------------------------------------------
# KPI catalog tests
# ---------------------------------------------------------------------------

class TestKPICatalog:
    def test_kpi_catalog_lists_all_kpis(self) -> None:
        catalog = default_kpi_catalog()
        kpis = catalog.list_all()
        assert len(kpis) == 8
        ids = {k.id for k in kpis}
        assert "net_revenue_uplift_pct" in ids
        assert "promo_roi_pct" in ids
        assert "gross_to_net_leakage_pct" in ids
        assert "purchase_cost_reduction_pct" in ids
        assert "contribution_margin_uplift_pct" in ids

    def test_kpi_catalog_computes_leakage(self, sample_fmcg_df: pd.DataFrame) -> None:
        catalog = default_kpi_catalog()
        leakage = catalog.compute("gross_to_net_leakage_pct", sample_fmcg_df)
        assert isinstance(leakage, float)
        assert 0.0 <= leakage <= 100.0


# ---------------------------------------------------------------------------
# Pilot selection tests
# ---------------------------------------------------------------------------

class TestPilot:
    def test_pilot_selection_returns_valid_cohort(self, sample_fmcg_df: pd.DataFrame) -> None:
        cohort = select_pilot_cohort(sample_fmcg_df)
        assert cohort.country in sample_fmcg_df["country"].unique()
        assert len(cohort.categories) >= 1
        assert len(cohort.control_stores) >= 1
        assert len(cohort.treatment_stores) >= 1
        assert cohort.row_count > 0

    def test_pilot_selection_respects_config(self, sample_fmcg_df: pd.DataFrame) -> None:
        config = PilotConfig(min_categories=1, max_categories=2, min_rows_per_category=1)
        cohort = select_pilot_cohort(sample_fmcg_df, config=config)
        assert len(cohort.categories) <= 2
