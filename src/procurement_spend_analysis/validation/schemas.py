from __future__ import annotations

from typing import Mapping

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame, Series


class SupplierSchema(pa.DataFrameModel):
    supplier_id: Series[str] = pa.Field(nullable=False, unique=True)
    supplier_name: Series[str] = pa.Field(nullable=False)
    category: Series[str] = pa.Field(nullable=False)
    country: Series[str] = pa.Field(nullable=False)
    payment_terms: Series[str] = pa.Field(nullable=False)
    currency: Series[str] = pa.Field(nullable=False, isin=["NGN", "USD", "EUR", "GBP", "CNY", "INR"])
    quality_rating: Series[float] = pa.Field(ge=0, le=5)
    is_approved: Series[bool] = pa.Field(nullable=False)
    risk_level: Series[str] = pa.Field(nullable=False, isin=["Low", "Medium", "High"])

    class Config:
        strict = False
        coerce = True


class MaterialsSchema(pa.DataFrameModel):
    material_id: Series[str] = pa.Field(nullable=False, unique=True)
    material_name: Series[str] = pa.Field(nullable=False)
    category: Series[str] = pa.Field(nullable=False)
    unit_of_measure: Series[str] = pa.Field(nullable=False)
    standard_price_ngn: Series[float] = pa.Field(ge=0)
    lead_time_days: Series[int] = pa.Field(ge=0, le=365)

    class Config:
        strict = False
        coerce = True


class PurchaseOrdersSchema(pa.DataFrameModel):
    po_number: Series[str] = pa.Field(nullable=False, unique=True)
    po_date: Series[pd.Timestamp] = pa.Field(nullable=False)
    supplier_id: Series[str] = pa.Field(nullable=False)
    supplier_name: Series[str] = pa.Field(nullable=True)
    material_id: Series[str] = pa.Field(nullable=False)
    material_name: Series[str] = pa.Field(nullable=True)
    category: Series[str] = pa.Field(nullable=False)
    quantity: Series[float] = pa.Field(ge=0)
    unit_price_ngn: Series[float] = pa.Field(ge=0)
    total_amount_ngn: Series[float] = pa.Field(ge=0)
    total_amount_usd: Series[float] = pa.Field(nullable=True, ge=0)
    currency: Series[str] = pa.Field(nullable=False)
    expected_delivery_date: Series[pd.Timestamp] = pa.Field(nullable=True)
    actual_delivery_date: Series[pd.Timestamp] = pa.Field(nullable=True)
    delivery_status: Series[str] = pa.Field(nullable=False)
    payment_status: Series[str] = pa.Field(nullable=False)
    buyer: Series[str] = pa.Field(nullable=True)
    plant_location: Series[str] = pa.Field(nullable=True)

    @pa.dataframe_check
    @classmethod
    def totals_match_quantity_times_price(cls, df: DataFrame["PurchaseOrdersSchema"]) -> bool:
        expected = (df["quantity"].fillna(0) * df["unit_price_ngn"].fillna(0)).round(2)
        actual = df["total_amount_ngn"].fillna(expected).round(2)
        return ((actual - expected).abs() <= 5.00).all()

    class Config:
        strict = False
        coerce = True


class QualityIncidentsSchema(pa.DataFrameModel):
    incident_id: Series[str] = pa.Field(nullable=False)
    po_number: Series[str] = pa.Field(nullable=True)
    supplier_id: Series[str] = pa.Field(nullable=True)
    incident_type: Series[str] = pa.Field(nullable=False)
    severity: Series[str] = pa.Field(nullable=False, isin=["Low", "Medium", "High", "Critical"])
    cost_impact_ngn: Series[float] = pa.Field(ge=0)

    class Config:
        strict = False
        coerce = True


def validate_canonical_tables(tables: Mapping[str, object]) -> dict[str, object]:
    """Validate normalized canonical tables with Pandera schemas."""

    validated = {
        "suppliers": SupplierSchema.validate(tables["suppliers"], lazy=True),
        "materials": MaterialsSchema.validate(tables["materials"], lazy=True),
        "purchase_orders": PurchaseOrdersSchema.validate(tables["purchase_orders"], lazy=True),
        "quality_incidents": QualityIncidentsSchema.validate(tables["quality_incidents"], lazy=True),
    }
    return validated
