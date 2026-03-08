"""Central analytics, ingestion, normalization, and export engine.

This module provides the shared data layer for both the Streamlit dashboard
and the Power BI export CLI.  It handles:

* **Column-alias normalization** — maps diverse ERP/CSV column names to a
  canonical schema so that uploads from SAP, Oracle, Coupa, or manual
  spreadsheets are accepted without manual renaming.
* **In-memory analytical store** — loads normalized DataFrames into a
  disposable SQLite instance for SQL-based analytics views.
* **Optimization and simulation** — orchestrates constrained allocation,
  Monte Carlo uncertainty, and scenario sensitivity runs.
* **Bundle packaging** — produces ZIP archives for Power BI handoff and
  company-upload template distribution.
"""

from __future__ import annotations

import io
import json
import logging
import sqlite3
import zipfile
from pathlib import Path
from typing import Mapping

import pandas as pd

from constrained_optimization import run_constrained_optimization
from generate_data import generate_dataset_bundle
from monte_carlo import monte_carlo_to_dataframe, run_monte_carlo_analysis
from optimization_engine import run_supplier_optimization
from scenario_analysis import run_sensitivity_analysis

logger = logging.getLogger(__name__)

# ── safety limits for CSV uploads ───────────────────────────────────────
MAX_UPLOAD_FILE_SIZE_MB = 50
MAX_UPLOAD_ROWS_PER_FILE = 500_000


PROJECT_ROOT = Path(__file__).resolve().parent
POWERBI_DIR = PROJECT_ROOT / "powerbi"
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "company_uploads"
SCENARIO_ASSUMPTIONS_PATH = PROJECT_ROOT / "scenario_assumptions.json"

RAW_DATASETS = {
    "suppliers": "suppliers.csv",
    "materials": "materials.csv",
    "purchase_orders": "purchase_orders.csv",
    "quality_incidents": "quality_incidents.csv",
}

CANONICAL_SCHEMAS = {
    "suppliers": {
        "required": ["supplier_id", "supplier_name"],
        "defaults": {
            "category": "Unclassified",
            "country": "Unknown",
            "payment_terms": "Net 30",
            "currency": "NGN",
            "quality_rating": 4.0,
            "is_approved": True,
            "risk_level": "Medium",
        },
        "aliases": {
            "supplier_id": ["supplier_id", "vendor_id", "vendor_code", "supplier_code", "id"],
            "supplier_name": ["supplier_name", "vendor_name", "name", "supplier", "vendor"],
            "category": ["category", "supplier_category", "spend_category"],
            "country": ["country", "supplier_country", "country_name"],
            "payment_terms": ["payment_terms", "payment_term", "terms"],
            "currency": ["currency", "invoice_currency", "po_currency"],
            "quality_rating": ["quality_rating", "quality_score", "supplier_score", "rating"],
            "is_approved": ["is_approved", "approved", "approved_flag", "is_active"],
            "risk_level": ["risk_level", "risk", "risk_rating", "vendor_risk"],
        },
    },
    "materials": {
        "required": ["material_id", "material_name"],
        "defaults": {
            "category": "Unclassified",
            "unit_of_measure": "PCS",
            "standard_price_ngn": 0.0,
            "lead_time_days": 30,
        },
        "aliases": {
            "material_id": ["material_id", "item_id", "sku", "material_code", "item_code"],
            "material_name": ["material_name", "item_name", "description", "material", "item_description"],
            "category": ["category", "material_category", "spend_category"],
            "unit_of_measure": ["unit_of_measure", "uom", "unit"],
            "standard_price_ngn": ["standard_price_ngn", "standard_cost", "std_price", "unit_standard_cost"],
            "lead_time_days": ["lead_time_days", "lead_time", "lead_days"],
        },
    },
    "purchase_orders": {
        "required": ["po_number", "po_date", "supplier_id", "material_id", "quantity"],
        "defaults": {
            "supplier_name": None,
            "material_name": None,
            "category": "Unclassified",
            "unit_price_ngn": 0.0,
            "total_amount_ngn": None,
            "total_amount_usd": None,
            "currency": "NGN",
            "expected_delivery_date": None,
            "actual_delivery_date": None,
            "delivery_status": "Delivered",
            "payment_status": "Paid",
            "buyer": "Unassigned",
            "plant_location": "Unknown",
        },
        "aliases": {
            "po_number": ["po_number", "po_id", "purchase_order", "purchase_order_number", "order_id"],
            "po_date": ["po_date", "order_date", "document_date", "created_date"],
            "supplier_id": ["supplier_id", "vendor_id", "supplier_code", "vendor_code"],
            "supplier_name": ["supplier_name", "vendor_name", "supplier", "vendor"],
            "material_id": ["material_id", "item_id", "sku", "material_code", "item_code"],
            "material_name": ["material_name", "item_name", "description", "item_description"],
            "category": ["category", "spend_category", "material_category"],
            "quantity": ["quantity", "qty", "ordered_qty", "order_quantity"],
            "unit_price_ngn": ["unit_price_ngn", "unit_price", "unit_cost", "net_price"],
            "total_amount_ngn": ["total_amount_ngn", "total_amount", "line_amount", "extended_amount", "spend_ngn"],
            "total_amount_usd": ["total_amount_usd", "spend_usd", "amount_usd"],
            "currency": ["currency", "invoice_currency", "po_currency"],
            "expected_delivery_date": ["expected_delivery_date", "promised_delivery_date", "expected_receipt_date"],
            "actual_delivery_date": ["actual_delivery_date", "delivery_date", "receipt_date", "actual_receipt_date"],
            "delivery_status": ["delivery_status", "status", "receipt_status"],
            "payment_status": ["payment_status", "invoice_status", "payment_state"],
            "buyer": ["buyer", "purchaser", "requestor", "buyer_name"],
            "plant_location": ["plant_location", "plant", "site", "location"],
        },
    },
    "quality_incidents": {
        "required": [],
        "defaults": {
            "incident_id": None,
            "po_number": None,
            "supplier_id": None,
            "incident_type": "Quality Defect",
            "severity": "Medium",
            "cost_impact_ngn": 0.0,
        },
        "aliases": {
            "incident_id": ["incident_id", "quality_incident_id", "issue_id", "defect_id"],
            "po_number": ["po_number", "po_id", "purchase_order", "order_id"],
            "supplier_id": ["supplier_id", "vendor_id", "vendor_code"],
            "incident_type": ["incident_type", "issue_type", "defect_type", "non_conformance_type"],
            "severity": ["severity", "priority", "impact_level"],
            "cost_impact_ngn": ["cost_impact_ngn", "cost_impact", "impact_amount", "loss_amount"],
        },
    },
}

FILENAME_HINTS = {
    "suppliers": ["supplier", "vendor"],
    "materials": ["material", "item", "sku", "product"],
    "purchase_orders": ["purchase_order", "po", "order"],
    "quality_incidents": ["quality", "incident", "defect", "issue", "non_conformance"],
}


class UploadValidationError(ValueError):
    """Raised when uploaded files cannot be normalized into the canonical model."""


def _validate_upload_size(payload: bytes, filename: str) -> None:
    """Guard against oversized or excessively long CSV uploads."""
    size_mb = len(payload) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_FILE_SIZE_MB:
        raise UploadValidationError(
            f"{filename} is {size_mb:.1f} MB — exceeds the {MAX_UPLOAD_FILE_SIZE_MB} MB limit."
        )


def load_assumptions() -> dict:
    """Load scenario assumptions from the project-level JSON config."""
    with open(SCENARIO_ASSUMPTIONS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _slug(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def _rename_columns(df: pd.DataFrame, dataset_key: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """Map incoming column names to the canonical schema via alias lookup."""
    schema = CANONICAL_SCHEMAS[dataset_key]
    aliases = schema["aliases"]
    rename_map: dict[str, str] = {}

    normalized_lookup = {_slug(column): column for column in df.columns}
    for canonical, known_aliases in aliases.items():
        for alias in known_aliases:
            matched = normalized_lookup.get(_slug(alias))
            if matched is not None:
                rename_map[matched] = canonical
                break

    renamed = df.rename(columns=rename_map).copy()
    return renamed, rename_map


def _coerce_bool(series: pd.Series) -> pd.Series:
    truthy = {"1", "true", "yes", "y", "approved", "active"}
    falsy = {"0", "false", "no", "n", "rejected", "inactive"}

    def convert(value):
        if pd.isna(value):
            return None
        if isinstance(value, bool):
            return value
        token = str(value).strip().lower()
        if token in truthy:
            return True
        if token in falsy:
            return False
        return None

    return series.map(convert)


def _apply_schema_defaults(df: pd.DataFrame, dataset_key: str) -> pd.DataFrame:
    """Fill missing columns with schema defaults and validate required columns."""
    schema = CANONICAL_SCHEMAS[dataset_key]
    defaults = schema["defaults"]

    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default

    missing_required = [col for col in schema["required"] if col not in df.columns]
    if missing_required:
        raise UploadValidationError(
            f"{dataset_key} is missing required columns after normalization: {', '.join(missing_required)}"
        )

    return df


def _coerce_dtypes(df: pd.DataFrame, dataset_key: str) -> pd.DataFrame:
    """Cast columns to expected dtypes with safe fallbacks."""
    if dataset_key == "suppliers":
        df["quality_rating"] = pd.to_numeric(df["quality_rating"], errors="coerce").fillna(4.0)
        df["is_approved"] = _coerce_bool(df["is_approved"]).fillna(True)
        df["risk_level"] = (
            df["risk_level"].astype(str).str.title().replace({"Nan": "Medium", "": "Medium"}).fillna("Medium")
        )
    elif dataset_key == "materials":
        df["standard_price_ngn"] = pd.to_numeric(df["standard_price_ngn"], errors="coerce").fillna(0.0)
        df["lead_time_days"] = pd.to_numeric(df["lead_time_days"], errors="coerce").fillna(30).astype(int)
    elif dataset_key == "purchase_orders":
        for column in [
            "quantity",
            "unit_price_ngn",
            "total_amount_ngn",
            "total_amount_usd",
        ]:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        for column in ["po_date", "expected_delivery_date", "actual_delivery_date"]:
            df[column] = pd.to_datetime(df[column], errors="coerce")

        df["currency"] = df["currency"].fillna("NGN").astype(str).str.upper()
        df["delivery_status"] = df["delivery_status"].fillna("Delivered")
        df["payment_status"] = df["payment_status"].fillna("Paid")
    elif dataset_key == "quality_incidents":
        df["cost_impact_ngn"] = pd.to_numeric(df["cost_impact_ngn"], errors="coerce").fillna(0.0)
        df["severity"] = df["severity"].fillna("Medium").astype(str).str.title()

    return df


def _normalize_dataframe(df: pd.DataFrame, dataset_key: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """Rename, default-fill, and type-coerce a single DataFrame."""
    normalized, rename_map = _rename_columns(df, dataset_key)
    normalized = _apply_schema_defaults(normalized, dataset_key)
    normalized = _coerce_dtypes(normalized, dataset_key)
    return normalized, rename_map


def infer_dataset_key(filename: str) -> str | None:
    """Guess the canonical dataset key from a filename (e.g. 'vendor_master.csv' → 'suppliers')."""
    token = _slug(Path(filename).stem)
    for dataset_key, hints in FILENAME_HINTS.items():
        if any(hint in token for hint in hints):
            return dataset_key
    return None


def _empty_quality_incidents() -> pd.DataFrame:
    return pd.DataFrame(columns=list(CANONICAL_SCHEMAS["quality_incidents"]["defaults"].keys()))


def normalize_raw_tables(raw_tables: Mapping[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, str]]]:
    """Normalize a dict of raw DataFrames into the canonical procurement model.

    Validates required datasets are present, applies alias renaming,
    default-fills missing columns, coerces dtypes, enriches PO rows
    with supplier/material names, and back-fills quality-incident IDs.

    Returns:
        Tuple of (normalized_tables dict, rename_maps dict).

    Raises:
        UploadValidationError: If a required dataset or column is missing.
    """
    normalized_tables: dict[str, pd.DataFrame] = {}
    rename_maps: dict[str, dict[str, str]] = {}

    for dataset_key in ["suppliers", "materials", "purchase_orders"]:
        if dataset_key not in raw_tables:
            raise UploadValidationError(f"Missing required dataset: {dataset_key}")
        normalized_tables[dataset_key], rename_maps[dataset_key] = _normalize_dataframe(raw_tables[dataset_key], dataset_key)

    if "quality_incidents" in raw_tables and not raw_tables["quality_incidents"].empty:
        normalized_tables["quality_incidents"], rename_maps["quality_incidents"] = _normalize_dataframe(
            raw_tables["quality_incidents"], "quality_incidents"
        )
    else:
        normalized_tables["quality_incidents"] = _empty_quality_incidents()
        rename_maps["quality_incidents"] = {}

    suppliers = normalized_tables["suppliers"].copy()
    materials = normalized_tables["materials"].copy()
    purchase_orders = normalized_tables["purchase_orders"].copy()

    purchase_orders = purchase_orders.merge(
        suppliers[["supplier_id", "supplier_name", "category"]].rename(columns={"category": "supplier_category"}),
        on="supplier_id",
        how="left",
    )
    purchase_orders = purchase_orders.merge(
        materials[["material_id", "material_name", "category"]].rename(columns={"category": "material_category"}),
        on="material_id",
        how="left",
    )

    purchase_orders["supplier_name"] = purchase_orders["supplier_name_x"].combine_first(purchase_orders["supplier_name_y"])
    purchase_orders["material_name"] = purchase_orders["material_name_x"].combine_first(purchase_orders["material_name_y"])
    purchase_orders["category"] = (
        purchase_orders["category"].replace({"": pd.NA}).combine_first(purchase_orders["material_category"]).combine_first(
            purchase_orders["supplier_category"]
        )
    )

    purchase_orders.drop(
        columns=[
            column
            for column in [
                "supplier_name_x",
                "supplier_name_y",
                "material_name_x",
                "material_name_y",
                "supplier_category",
                "material_category",
            ]
            if column in purchase_orders.columns
        ],
        inplace=True,
    )

    purchase_orders["quantity"] = purchase_orders["quantity"].fillna(0)
    purchase_orders["unit_price_ngn"] = purchase_orders["unit_price_ngn"].fillna(0.0)
    purchase_orders["total_amount_ngn"] = purchase_orders["total_amount_ngn"].fillna(
        purchase_orders["quantity"] * purchase_orders["unit_price_ngn"]
    )
    purchase_orders["expected_delivery_date"] = purchase_orders["expected_delivery_date"].fillna(
        purchase_orders["po_date"] + pd.to_timedelta(30, unit="D")
    )
    purchase_orders["delivery_status"] = purchase_orders["delivery_status"].fillna("Delivered")
    purchase_orders["payment_status"] = purchase_orders["payment_status"].fillna("Paid")

    quality_incidents = normalized_tables["quality_incidents"].copy()
    if quality_incidents["incident_id"].isna().all():
        quality_incidents["incident_id"] = [f"QI{i+1:05d}" for i in range(len(quality_incidents))]
    if quality_incidents["supplier_id"].isna().any() and not purchase_orders.empty:
        supplier_lookup = purchase_orders[["po_number", "supplier_id"]].drop_duplicates()
        quality_incidents = quality_incidents.merge(supplier_lookup, on="po_number", how="left", suffixes=("", "_lookup"))
        quality_incidents["supplier_id"] = quality_incidents["supplier_id"].combine_first(quality_incidents["supplier_id_lookup"])
        quality_incidents.drop(columns=[col for col in ["supplier_id_lookup"] if col in quality_incidents.columns], inplace=True)

    normalized_tables["purchase_orders"] = purchase_orders
    normalized_tables["quality_incidents"] = quality_incidents
    return normalized_tables, rename_maps


def _load_to_sqlite(normalized_tables: Mapping[str, pd.DataFrame]) -> sqlite3.Connection:
    """Create a disposable in-memory SQLite store with analytical views."""
    conn = sqlite3.connect(":memory:")
    suppliers_df = normalized_tables["suppliers"].copy()
    materials_df = normalized_tables["materials"].copy()
    pos_df = normalized_tables["purchase_orders"].copy()
    incidents_df = normalized_tables["quality_incidents"].copy()

    suppliers_df.to_sql("suppliers", conn, if_exists="replace", index=False)
    materials_df.to_sql("materials", conn, if_exists="replace", index=False)
    pos_df.to_sql("purchase_orders", conn, if_exists="replace", index=False)
    incidents_df.to_sql("quality_incidents", conn, if_exists="replace", index=False)

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE VIEW vw_supplier_performance AS
        SELECT
            s.supplier_id,
            s.supplier_name,
            s.category,
            s.country,
            s.risk_level,
            s.quality_rating,
            COUNT(DISTINCT po.po_number) as total_orders,
            ROUND(SUM(po.total_amount_ngn), 2) as total_spend_ngn,
            ROUND(AVG(po.total_amount_ngn), 2) as avg_order_value,
            ROUND(
                SUM(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END), 0),
                2
            ) as on_time_delivery_pct,
            COUNT(DISTINCT qi.incident_id) as quality_incidents,
            ROUND(COALESCE(SUM(qi.cost_impact_ngn), 0), 2) as total_quality_cost
        FROM suppliers s
        LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
        LEFT JOIN quality_incidents qi ON po.po_number = qi.po_number
        GROUP BY s.supplier_id, s.supplier_name, s.category, s.country, s.risk_level, s.quality_rating
        """
    )
    conn.commit()
    return conn


def _grade_supplier_performance(row: pd.Series) -> str:
    """Assign a letter grade (A–E) based on OTD % and incident count."""
    otd = float(row.get("on_time_delivery_pct") or 0)
    incidents = float(row.get("quality_incidents") or 0)
    if otd >= 95 and incidents <= 1:
        return "A"
    if otd >= 90 and incidents <= 2:
        return "B"
    if otd >= 80 and incidents <= 4:
        return "C"
    if otd >= 70 and incidents <= 6:
        return "D"
    return "E"


def _build_quality_report(normalized_tables: Mapping[str, pd.DataFrame]) -> dict:
    """Compute data-quality diagnostics (row counts, nulls, duplicates, unmapped keys)."""
    purchase_orders = normalized_tables["purchase_orders"]
    quality_incidents = normalized_tables["quality_incidents"]
    suppliers = normalized_tables["suppliers"]
    materials = normalized_tables["materials"]

    return {
        "row_counts": {name: int(len(df)) for name, df in normalized_tables.items()},
        "null_cells": {name: int(df.isna().sum().sum()) for name, df in normalized_tables.items()},
        "duplicate_rows": {name: int(df.duplicated().sum()) for name, df in normalized_tables.items()},
        "unmapped_supplier_ids": int((~purchase_orders["supplier_id"].isin(suppliers["supplier_id"])).sum()),
        "unmapped_material_ids": int((~purchase_orders["material_id"].isin(materials["material_id"])).sum()),
        "quality_incidents_without_po": int((~quality_incidents["po_number"].fillna("").isin(purchase_orders["po_number"])) .sum())
        if not quality_incidents.empty
        else 0,
    }


def _build_analytics(normalized_tables: Mapping[str, pd.DataFrame], source_label: str) -> dict:
    """Run the full analytics pipeline and return a self-contained bundle dict.

    Steps: SQL aggregations → supplier grading → optimization → Monte Carlo →
    scenario sensitivity → summary table assembly.
    """
    logger.info("Building analytics bundle (source=%s)", source_label)
    conn = _load_to_sqlite(normalized_tables)
    assumptions = load_assumptions()
    purchase_orders = normalized_tables["purchase_orders"]

    total_spend = float(purchase_orders["total_amount_ngn"].sum())

    category_spend = pd.read_sql(
        """
        SELECT
            category,
            ROUND(SUM(total_amount_ngn), 2) AS total_spend_ngn,
            ROUND(SUM(total_amount_ngn) * 100.0 / NULLIF((SELECT SUM(total_amount_ngn) FROM purchase_orders), 0), 2) AS pct_of_total
        FROM purchase_orders
        GROUP BY category
        ORDER BY total_spend_ngn DESC
        """,
        conn,
    )

    supplier_performance = pd.read_sql(
        """
        SELECT
            supplier_name,
            category,
            country,
            total_orders,
            total_spend_ngn,
            on_time_delivery_pct,
            quality_incidents,
            total_quality_cost
        FROM vw_supplier_performance
        WHERE total_orders > 0
        ORDER BY total_spend_ngn DESC
        """,
        conn,
    )
    supplier_performance["performance_grade"] = supplier_performance.apply(_grade_supplier_performance, axis=1)

    price_variance = pd.read_sql(
        """
        SELECT
            material_name,
            category,
            COUNT(DISTINCT supplier_id) AS supplier_count,
            ROUND(MIN(unit_price_ngn), 2) AS min_price,
            ROUND(AVG(unit_price_ngn), 2) AS avg_price,
            ROUND(MAX(unit_price_ngn), 2) AS max_price,
            ROUND((MAX(unit_price_ngn) - MIN(unit_price_ngn)) / NULLIF(MIN(unit_price_ngn), 0) * 100, 2) AS price_variance_pct,
            ROUND(SUM(total_amount_ngn) * (AVG(unit_price_ngn) - MIN(unit_price_ngn)) / NULLIF(AVG(unit_price_ngn), 0), 0) AS potential_savings_ngn
        FROM purchase_orders
        GROUP BY material_name, category
        HAVING supplier_count > 1 AND potential_savings_ngn > 0
        ORDER BY potential_savings_ngn DESC
        LIMIT 20
        """,
        conn,
    )

    monthly_spend = purchase_orders.copy()
    monthly_spend["month"] = pd.to_datetime(monthly_spend["po_date"], errors="coerce").dt.strftime("%Y-%m")
    monthly_spend_by_category = (
        monthly_spend.dropna(subset=["month"]).groupby(["month", "category"], as_index=False)["total_amount_ngn"].sum()
        .rename(columns={"total_amount_ngn": "total_spend_ngn"})
        .sort_values(["month", "category"])
    )

    price_standardization_savings = float(price_variance["potential_savings_ngn"].sum())

    poor_performers = supplier_performance[
        ((supplier_performance["on_time_delivery_pct"] < 80) | (supplier_performance["quality_incidents"] > 2))
        & (supplier_performance["total_orders"] > 5)
    ]
    quality_cost = float(poor_performers["total_quality_cost"].sum())
    delivery_cost = float(poor_performers["total_spend_ngn"].sum()) * 0.03
    performance_improvement_savings = quality_cost + delivery_cost

    fragmentation = (
        purchase_orders.groupby("category")
        .agg(supplier_count=("supplier_id", "nunique"), total_spend=("total_amount_ngn", "sum"))
        .reset_index()
    )
    consolidation_savings = float(fragmentation.loc[fragmentation["supplier_count"] > 8, "total_spend"].sum() * 0.06)

    maverick = purchase_orders.merge(
        normalized_tables["suppliers"][["supplier_id", "risk_level", "is_approved"]], on="supplier_id", how="left"
    )
    maverick = maverick[(maverick["is_approved"] == False) | (maverick["risk_level"] == "High")]
    maverick_spend = float(maverick["total_amount_ngn"].sum()) if not maverick.empty else 0.0

    usd_orders = purchase_orders[(purchase_orders["currency"] == "USD") & (purchase_orders["total_amount_usd"].fillna(0) > 0)].copy()
    usd_spend = float(usd_orders["total_amount_usd"].sum()) if not usd_orders.empty else 0.0
    if not usd_orders.empty:
        fx_series = usd_orders["total_amount_ngn"] / usd_orders["total_amount_usd"]
        fx_volatility = float(((fx_series.max() - fx_series.min()) / fx_series.min()) * 100) if fx_series.min() > 0 else 0.0
    else:
        fx_volatility = 0.0

    insights = {
        "total_spend": total_spend,
        "price_standardization_savings": price_standardization_savings,
        "performance_improvement_savings": performance_improvement_savings,
        "consolidation_savings": consolidation_savings,
        "maverick_spend": maverick_spend,
        "usd_spend": usd_spend,
        "fx_volatility": fx_volatility,
    }
    insights["total_savings"] = (
        insights["price_standardization_savings"]
        + insights["performance_improvement_savings"]
        + insights["consolidation_savings"]
    )
    insights["savings_percentage"] = (insights["total_savings"] / total_spend * 100) if total_spend > 0 else 0.0

    optimization_df, optimization_summary = run_supplier_optimization(
        conn=conn,
        max_suppliers_per_category=int(assumptions["supplier_optimization"].get("max_suppliers_per_category", 3)),
        min_supplier_share=float(assumptions["supplier_optimization"].get("min_supplier_share", 0.15)),
        score_weights=assumptions["supplier_optimization"].get("score_weights"),
    )
    constrained_df, constrained_summary = run_constrained_optimization(
        conn=conn,
        constraints=assumptions["constraints"]["standard"],
    )
    sensitivity_df = run_sensitivity_analysis(insights=insights, scenario_factors=assumptions["sensitivity_scenarios"])
    mc_results = run_monte_carlo_analysis(
        base_insights=insights,
        num_simulations=assumptions["monte_carlo"].get("num_simulations", 10000),
        random_seed=assumptions["monte_carlo"].get("random_seed", 42),
        uncertainty_params=assumptions["monte_carlo"].get("uncertainty_parameters", {}),
    )
    mc_df = monte_carlo_to_dataframe(mc_results)

    insights.update(optimization_summary)
    insights.update(constrained_summary)
    insights.update(mc_results)

    summary_rows = [
        ("Total Spend", insights["total_spend"], "NGN"),
        ("Price Standardization Savings", insights["price_standardization_savings"], "NGN"),
        ("Supplier Performance Savings", insights["performance_improvement_savings"], "NGN"),
        ("Supplier Consolidation Savings", insights["consolidation_savings"], "NGN"),
        ("Optimization Savings", insights.get("optimization_savings_ngn", 0.0), "NGN"),
        ("Total Savings Potential", insights["total_savings"], "NGN"),
        ("Savings Percentage", insights["savings_percentage"], "percent"),
        ("Optimization Savings Percentage", insights.get("optimization_savings_pct", 0.0), "percent"),
        ("Constrained Savings", insights.get("constrained_savings_ngn", 0.0), "NGN"),
        ("Constrained Savings Percentage", insights.get("constrained_savings_pct", 0.0), "percent"),
        ("Maverick Spend", insights["maverick_spend"], "NGN"),
        ("USD Spend", insights["usd_spend"], "USD"),
        ("FX Volatility", insights["fx_volatility"], "percent"),
        ("Monte Carlo P05 Savings", insights.get("total_savings_p05_ngn", 0.0), "NGN"),
        ("Monte Carlo Median Savings", insights.get("total_savings_median_ngn", 0.0), "NGN"),
        ("Monte Carlo P95 Savings", insights.get("total_savings_p95_ngn", 0.0), "NGN"),
    ]
    procurement_insights_summary = pd.DataFrame(summary_rows, columns=["metric", "value", "unit"])

    quality_report = _build_quality_report(normalized_tables)

    conn.close()
    return {
        "raw": dict(normalized_tables),
        "analytics": {
            "procurement_insights_summary": procurement_insights_summary,
            "category_spend": category_spend,
            "supplier_performance": supplier_performance,
            "price_variance_top20": price_variance,
            "monthly_spend_by_category": monthly_spend_by_category,
            "supplier_optimization_recommendations": optimization_df,
            "constrained_supplier_recommendations": constrained_df,
            "savings_scenarios": sensitivity_df,
            "monte_carlo_uncertainty_bounds": mc_df,
        },
        "insights": insights,
        "metadata": {
            "source_label": source_label,
            "quality_report": quality_report,
        },
    }


def load_demo_bundle() -> dict:
    """Load the bundled demo CSV files and build an analytics bundle."""
    raw_tables = {
        dataset_key: pd.read_csv(PROJECT_ROOT / filename)
        for dataset_key, filename in RAW_DATASETS.items()
    }
    normalized_tables, _ = normalize_raw_tables(raw_tables)
    return _build_analytics(normalized_tables, source_label="Bundled demo dataset")


def generate_demo_bundle(num_orders: int = 2500, seed: int = 42, num_quality_incidents: int = 150) -> dict:
    raw_tables = generate_dataset_bundle(
        num_orders=num_orders,
        num_quality_incidents=num_quality_incidents,
        seed=seed,
    )
    normalized_tables, _ = normalize_raw_tables(raw_tables)
    return _build_analytics(normalized_tables, source_label="Generated realistic demo dataset")


def build_bundle_from_uploaded_frames(
    uploaded_frames: Mapping[str, pd.DataFrame],
    source_label: str = "Uploaded company data",
) -> dict:
    """Normalize caller-provided DataFrames and return an analytics bundle."""
    normalized_tables, rename_maps = normalize_raw_tables(uploaded_frames)
    bundle = _build_analytics(normalized_tables, source_label=source_label)
    bundle["metadata"]["rename_maps"] = rename_maps
    return bundle


def build_bundle_from_upload_bytes(
    uploaded_files: Mapping[str, bytes],
    source_label: str = "Uploaded company data",
) -> dict:
    """Parse uploaded CSV bytes, validate sizes, normalize, and build bundle.

    Raises:
        UploadValidationError: On oversized files, excessive row counts,
            unrecognised filenames, or missing required datasets.
    """
    raw_tables: dict[str, pd.DataFrame] = {}
    for filename, payload in uploaded_files.items():
        _validate_upload_size(payload, filename)
        dataset_key = infer_dataset_key(filename)
        if dataset_key is None:
            logger.warning("Skipping unrecognised upload: %s", filename)
            continue
        df = pd.read_csv(io.BytesIO(payload))
        if len(df) > MAX_UPLOAD_ROWS_PER_FILE:
            raise UploadValidationError(
                f"{filename} has {len(df):,} rows — exceeds the {MAX_UPLOAD_ROWS_PER_FILE:,} row limit."
            )
        raw_tables[dataset_key] = df

    if not raw_tables:
        raise UploadValidationError("No supported CSV files were detected. Upload supplier, material, PO, and optional quality files.")

    return build_bundle_from_uploaded_frames(raw_tables, source_label=source_label)


def export_powerbi_pack(bundle: dict) -> bytes:
    """Package analytics exports, raw CSVs, and Power BI assets into a ZIP."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, df in bundle["analytics"].items():
            archive.writestr(f"exports/{name}.csv", df.to_csv(index=False))

        for name, df in bundle["raw"].items():
            archive.writestr(f"normalized_raw/{name}.csv", df.to_csv(index=False))

        archive.writestr(
            "exports/data_quality_report.json",
            json.dumps(bundle["metadata"]["quality_report"], indent=2),
        )
        archive.writestr(
            "exports/streamlit_source.json",
            json.dumps({"source_label": bundle["metadata"].get("source_label", "Unknown")}, indent=2),
        )

        for asset_name in [
            "DAX_MEASURES.md",
            "PHASE3_POWERBI_HANDOFF.md",
            "POWERBI_DEPLOYMENT_GUIDE.md",
            "POWERBI_PBIT_STARTER_SPEC.json",
            "POWERBI_PAGE_BUILD_SHEET.md",
            "powerbi_theme.json",
            "powerbi_field_mapping.csv",
        ]:
            asset_path = POWERBI_DIR / asset_name
            if asset_path.exists():
                archive.writestr(f"powerbi/{asset_name}", asset_path.read_text(encoding="utf-8"))

    return buffer.getvalue()


def upload_schema_reference() -> pd.DataFrame:
    """Return a human-readable summary of the canonical upload schemas."""
    rows = []
    for dataset_key, schema in CANONICAL_SCHEMAS.items():
        rows.append(
            {
                "dataset": dataset_key,
                "required_columns": ", ".join(schema["required"]) if schema["required"] else "optional",
                "accepted_alias_examples": "; ".join(
                    f"{canonical}: {', '.join(aliases[:3])}" for canonical, aliases in schema["aliases"].items()
                ),
            }
        )
    return pd.DataFrame(rows)


def template_file_paths() -> dict[str, Path]:
    """Return a mapping of logical names to template CSV paths."""
    return {
        "suppliers": TEMPLATES_DIR / "suppliers_template.csv",
        "materials": TEMPLATES_DIR / "materials_template.csv",
        "purchase_orders": TEMPLATES_DIR / "purchase_orders_template.csv",
        "quality_incidents": TEMPLATES_DIR / "quality_incidents_template.csv",
        "readme": TEMPLATES_DIR / "README.md",
    }


def export_upload_template_pack() -> bytes:
    """ZIP all company-upload CSV templates for one-click download."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for logical_name, file_path in template_file_paths().items():
            if file_path.exists():
                archive.writestr(f"company_upload_templates/{file_path.name}", file_path.read_bytes())
    return buffer.getvalue()


def prepare_dashboard_context(
    bundle: dict,
    selected_categories: list[str] | None = None,
    start_date=None,
    end_date=None,
) -> dict:
    """Apply category and date filters to a bundle and return a ready-to-render context.

    The returned dict contains filtered DataFrames, computed metrics, and
    pass-through references to the full analytics and insights dicts.
    """
    raw = bundle["raw"]
    analytics = bundle["analytics"]
    insights = bundle["insights"]
    metadata = bundle["metadata"]

    purchase_orders = raw["purchase_orders"].copy()
    purchase_orders["po_date"] = pd.to_datetime(purchase_orders["po_date"], errors="coerce")

    all_categories = sorted([category for category in purchase_orders["category"].dropna().unique().tolist()])
    if not selected_categories:
        selected_categories = all_categories

    filtered_pos = purchase_orders[purchase_orders["category"].isin(selected_categories)].copy()
    if start_date is not None and end_date is not None:
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date)
        filtered_pos = filtered_pos[(filtered_pos["po_date"] >= start_ts) & (filtered_pos["po_date"] <= end_ts)]

    filtered_suppliers = analytics["supplier_performance"][analytics["supplier_performance"]["category"].isin(selected_categories)].copy()
    filtered_price_variance = analytics["price_variance_top20"][analytics["price_variance_top20"]["category"].isin(selected_categories)].copy()
    filtered_monthly = analytics["monthly_spend_by_category"][analytics["monthly_spend_by_category"]["category"].isin(selected_categories)].copy()
    filtered_category_spend = analytics["category_spend"][analytics["category_spend"]["category"].isin(selected_categories)].copy()
    filtered_optimization = analytics["supplier_optimization_recommendations"][analytics["supplier_optimization_recommendations"]["category"].isin(selected_categories)].copy()
    filtered_constrained = analytics["constrained_supplier_recommendations"][analytics["constrained_supplier_recommendations"]["category"].isin(selected_categories)].copy()

    supplier_lookup = raw["suppliers"]["supplier_id risk_level is_approved".split()].drop_duplicates()
    filtered_maverick = filtered_pos.merge(supplier_lookup, on="supplier_id", how="left")
    filtered_maverick = filtered_maverick[
        (filtered_maverick["is_approved"] == False) | (filtered_maverick["risk_level"] == "High")
    ]

    filtered_total_spend = float(filtered_pos["total_amount_ngn"].sum()) if not filtered_pos.empty else 0.0
    filtered_maverick_spend = float(filtered_maverick["total_amount_ngn"].sum()) if not filtered_maverick.empty else 0.0
    filtered_savings = float(filtered_price_variance["potential_savings_ngn"].sum()) if not filtered_price_variance.empty else 0.0
    filtered_supplier_count = int(filtered_pos["supplier_id"].nunique()) if not filtered_pos.empty else 0

    return {
        "raw": raw,
        "analytics": analytics,
        "insights": insights,
        "metadata": metadata,
        "all_categories": all_categories,
        "purchase_orders": purchase_orders,
        "filtered_pos": filtered_pos,
        "filtered_suppliers": filtered_suppliers,
        "filtered_price_variance": filtered_price_variance,
        "filtered_monthly": filtered_monthly,
        "filtered_category_spend": filtered_category_spend,
        "filtered_optimization": filtered_optimization,
        "filtered_constrained": filtered_constrained,
        "filtered_maverick": filtered_maverick,
        "metrics": {
            "filtered_total_spend": filtered_total_spend,
            "filtered_maverick_spend": filtered_maverick_spend,
            "filtered_savings": filtered_savings,
            "filtered_supplier_count": filtered_supplier_count,
        },
    }
