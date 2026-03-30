"""Canonical data models and Pandera schema for the FMCG daily-sales dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd
import pandera.pandas as pa
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Pandera schema — validates all 32 columns of the FMCG tab-separated CSV
# ---------------------------------------------------------------------------

FMCGSalesSchema = pa.DataFrameSchema(
    columns={
        "date": pa.Column(str, nullable=False),
        "year": pa.Column(int, nullable=False, checks=pa.Check.in_range(2000, 2100)),
        "month": pa.Column(int, nullable=False, checks=pa.Check.in_range(1, 12)),
        "day": pa.Column(int, nullable=False, checks=pa.Check.in_range(1, 31)),
        "weekofyear": pa.Column(int, nullable=False, checks=pa.Check.in_range(1, 53)),
        "weekday": pa.Column(int, nullable=False, checks=pa.Check.in_range(0, 6)),
        "is_weekend": pa.Column(int, nullable=False, checks=pa.Check.isin([0, 1])),
        "is_holiday": pa.Column(int, nullable=False, checks=pa.Check.isin([0, 1])),
        "temperature": pa.Column(float, nullable=False),
        "rain_mm": pa.Column(
            float, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "store_id": pa.Column(str, nullable=False),
        "country": pa.Column(str, nullable=False),
        "city": pa.Column(str, nullable=False),
        "channel": pa.Column(str, nullable=False),
        "latitude": pa.Column(float, nullable=False),
        "longitude": pa.Column(float, nullable=False),
        "sku_id": pa.Column(str, nullable=False),
        "sku_name": pa.Column(str, nullable=False),
        "category": pa.Column(str, nullable=False),
        "subcategory": pa.Column(str, nullable=False),
        "brand": pa.Column(str, nullable=False),
        "units_sold": pa.Column(
            int, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "list_price": pa.Column(float, nullable=False, checks=pa.Check.greater_than(0)),
        "discount_pct": pa.Column(
            float, nullable=False, checks=pa.Check.in_range(0.0, 1.0)
        ),
        "promo_flag": pa.Column(int, nullable=False, checks=pa.Check.isin([0, 1])),
        "gross_sales": pa.Column(
            float, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "net_sales": pa.Column(
            float, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "stock_on_hand": pa.Column(
            int, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "stock_out_flag": pa.Column(int, nullable=False, checks=pa.Check.isin([0, 1])),
        "lead_time_days": pa.Column(
            int, nullable=False, checks=pa.Check.greater_than_or_equal_to(0)
        ),
        "supplier_id": pa.Column(str, nullable=False),
        "purchase_cost": pa.Column(
            float, nullable=False, checks=pa.Check.greater_than(0)
        ),
        "margin_pct": pa.Column(float, nullable=False),
    },
    strict=False,
    coerce=True,
)

# ---------------------------------------------------------------------------
# Pydantic v2 models
# ---------------------------------------------------------------------------


class StoreEntity(BaseModel):
    """A unique retail store location."""

    model_config = {"frozen": True}

    store_id: str
    country: str
    city: str
    channel: str
    latitude: float
    longitude: float


class SKUEntity(BaseModel):
    """A stock-keeping unit with category hierarchy."""

    model_config = {"frozen": True}

    sku_id: str
    sku_name: str
    category: str
    subcategory: str
    brand: str


class SupplierEntity(BaseModel):
    """Minimal supplier reference."""

    model_config = {"frozen": True}

    supplier_id: str


class FMCGSalesRecord(BaseModel):
    """Single row of the FMCG daily-sales dataset."""

    model_config = {"frozen": True}

    date: str
    year: int
    month: int
    day: int
    weekofyear: int
    weekday: int
    is_weekend: int
    is_holiday: int
    temperature: float
    rain_mm: float
    store_id: str
    country: str
    city: str
    channel: str
    latitude: float
    longitude: float
    sku_id: str
    sku_name: str
    category: str
    subcategory: str
    brand: str
    units_sold: int
    list_price: float
    discount_pct: float
    promo_flag: int
    gross_sales: float
    net_sales: float
    stock_on_hand: int
    stock_out_flag: int
    lead_time_days: int
    supplier_id: str
    purchase_cost: float
    margin_pct: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate_fmcg_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate *df* against :data:`FMCGSalesSchema` and return the coerced frame."""
    return FMCGSalesSchema.validate(df, lazy=True)


def load_fmcg_csv(path: Union[str, Path], sep: str = "\t") -> pd.DataFrame:
    """Read a tab-separated FMCG CSV and validate it against the canonical schema."""
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"FMCG CSV not found: {resolved}")
    df = pd.read_csv(resolved, sep=sep)
    # Strip whitespace from column names that may come from messy exports
    df.columns = [c.strip() for c in df.columns]
    return validate_fmcg_dataframe(df)
