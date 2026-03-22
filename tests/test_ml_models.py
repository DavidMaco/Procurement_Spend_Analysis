import pandas as pd

from procurement_spend_analysis.ml import (
    detect_procurement_anomalies,
    forecast_category_demand,
)


def _purchase_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "po_number": [f"PO{i:03d}" for i in range(1, 13)],
            "po_date": pd.date_range("2024-01-01", periods=12, freq="MS"),
            "category": ["Packaging"] * 12,
            "quantity": [100, 120, 110, 130, 125, 140, 145, 138, 150, 160, 158, 170],
            "unit_price_ngn": [
                1000,
                1005,
                998,
                1002,
                1010,
                1007,
                1008,
                1003,
                1004,
                1006,
                1002,
                4500,
            ],
            "total_amount_ngn": [
                100000,
                120600,
                109780,
                130260,
                126250,
                140980,
                146160,
                138414,
                150600,
                160960,
                158316,
                765000,
            ],
            "currency": ["NGN"] * 12,
        }
    )


def test_forecast_category_demand_returns_future_rows():
    forecast = forecast_category_demand(_purchase_orders(), periods=2)
    assert len(forecast) == 2
    assert (forecast["forecast_quantity"] >= 0).all()


def test_detect_procurement_anomalies_flags_outlier_order():
    anomalies = detect_procurement_anomalies(_purchase_orders(), contamination=0.1)
    flagged = anomalies[anomalies["is_anomaly"]]
    assert not flagged.empty
    assert flagged["unit_price_ngn"].max() == 4500
