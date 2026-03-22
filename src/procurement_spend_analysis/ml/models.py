from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor


def forecast_category_demand(
    purchase_orders: pd.DataFrame, periods: int = 3
) -> pd.DataFrame:
    """Forecast category-level monthly demand using calendar features and RandomForest regression."""
    df = purchase_orders.copy()
    df["po_date"] = pd.to_datetime(df["po_date"], errors="coerce")
    df = df.dropna(subset=["po_date"])
    df["month"] = df["po_date"].dt.to_period("M").dt.to_timestamp()

    monthly = df.groupby(["category", "month"], as_index=False)["quantity"].sum()
    forecasts = []

    for category, frame in monthly.groupby("category"):
        scoped = frame.sort_values("month").reset_index(drop=True)
        scoped["month_idx"] = np.arange(len(scoped))
        scoped["month_num"] = scoped["month"].dt.month
        scoped["quarter"] = scoped["month"].dt.quarter

        if len(scoped) < 4:
            baseline = float(scoped["quantity"].mean()) if not scoped.empty else 0.0
            for step in range(1, periods + 1):
                next_month = (
                    scoped["month"].max() + pd.offsets.MonthBegin(step)
                    if not scoped.empty
                    else pd.Timestamp.today().floor("D")
                )
                forecasts.append(
                    {
                        "category": category,
                        "month": next_month,
                        "forecast_quantity": baseline,
                        "model": "mean_fallback",
                    }
                )
            continue

        model = RandomForestRegressor(n_estimators=200, random_state=42)
        features = scoped[["month_idx", "month_num", "quarter"]]
        model.fit(features, scoped["quantity"])
        last_idx = int(scoped["month_idx"].max())
        last_month = scoped["month"].max()
        for step in range(1, periods + 1):
            next_month = last_month + pd.offsets.MonthBegin(step)
            row = pd.DataFrame(
                {
                    "month_idx": [last_idx + step],
                    "month_num": [next_month.month],
                    "quarter": [next_month.quarter],
                }
            )
            pred = float(model.predict(row)[0])
            forecasts.append(
                {
                    "category": category,
                    "month": next_month,
                    "forecast_quantity": max(0.0, pred),
                    "model": "random_forest",
                }
            )

    return pd.DataFrame(forecasts)


def detect_procurement_anomalies(
    purchase_orders: pd.DataFrame, contamination: float = 0.03
) -> pd.DataFrame:
    """Flag anomalous purchase orders using Isolation Forest on spend and operational features."""
    df = purchase_orders.copy()
    if df.empty:
        return df.assign(
            anomaly_score=pd.Series(dtype=float), is_anomaly=pd.Series(dtype=bool)
        )

    model_input = pd.DataFrame(
        {
            "quantity": pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0),
            "unit_price_ngn": pd.to_numeric(
                df["unit_price_ngn"], errors="coerce"
            ).fillna(0.0),
            "total_amount_ngn": pd.to_numeric(
                df["total_amount_ngn"], errors="coerce"
            ).fillna(0.0),
            "currency_is_usd": df.get("currency", "NGN")
            .astype(str)
            .eq("USD")
            .astype(int),
        }
    )
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(model_input)
    scores = model.decision_function(model_input)
    labels = model.predict(model_input)

    result = df.copy()
    result["anomaly_score"] = scores
    result["is_anomaly"] = labels == -1
    return result.sort_values("anomaly_score")
