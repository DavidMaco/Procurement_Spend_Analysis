from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from io import BytesIO

import httpx
import pandas as pd

from procurement_spend_analysis.api.app import app


def _headers(*roles: str, user_id: str = "demo-user") -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Roles": ",".join(roles)}


def _make_fmcg_upload(*, discount_pct: float) -> BytesIO:
    gross_sales = 100.0
    net_sales = gross_sales * (1 - discount_pct)
    margin_pct = round((net_sales - 60.0) / net_sales, 3)
    df = pd.DataFrame(
        [
            {
                "date": "1/1/2021",
                "year": 2021,
                "month": 1,
                "day": 1,
                "weekofyear": 1,
                "weekday": 4,
                "is_weekend": 0,
                "is_holiday": 0,
                "temperature": 25.0,
                "rain_mm": 0.0,
                "store_id": "STORE001",
                "country": "Germany",
                "city": "Berlin",
                "channel": "Hypermarket",
                "latitude": 52.52,
                "longitude": 13.39,
                "sku_id": "SKU001",
                "sku_name": "BrandA Shampoo",
                "category": "Personal Care",
                "subcategory": "Shampoo",
                "brand": "BrandA",
                "units_sold": 10,
                "list_price": 10.0,
                "discount_pct": discount_pct,
                "promo_flag": 1,
                "gross_sales": gross_sales,
                "net_sales": round(net_sales, 2),
                "stock_on_hand": 25,
                "stock_out_flag": 0,
                "lead_time_days": 5,
                "supplier_id": "S001",
                "purchase_cost": 6.0,
                "margin_pct": margin_pct,
            }
        ]
    )
    return BytesIO(df.to_csv(index=False).encode("utf-8"))


async def _run() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        response = await client.get("/fmcg/metrics")
        assert response.status_code == 401

        response = await client.get(
            "/fmcg/metrics",
            headers=_headers("analyst", user_id="analyst-1"),
        )
        assert response.status_code == 200
        assert any(metric["name"] == "gross_sales" for metric in response.json())

        response = await client.get("/fmcg/alerts/rules", headers=_headers("viewer"))
        assert response.status_code == 200

        response = await client.post(
            "/fmcg/alerts/evaluate",
            headers=_headers("viewer"),
            files={
                "baseline_file": ("baseline.csv", _make_fmcg_upload(discount_pct=0.05), "text/csv"),
                "current_file": ("current.csv", _make_fmcg_upload(discount_pct=0.30), "text/csv"),
            },
        )
        assert response.status_code == 200
        assert response.json()["alert_count"] >= 1

        response = await client.post(
            "/fmcg/events/recommendations",
            headers=_headers("analyst"),
            json={
                "model_id": "promo_v2",
                "model_version": "2.1.0",
                "input_snapshot_ref": "s3://bucket/snap_002.parquet",
                "recommendation_type": "promo_depth",
                "recommendation_payload": {"sku": "SKU001", "suggested_discount": 0.12},
                "confidence_score": 0.91,
            },
        )
        assert response.status_code == 200
        event = response.json()

        response = await client.post(
            f"/fmcg/events/{event['event_id']}/approve",
            headers=_headers("approver"),
            json={"approver_id": "approver-7"},
        )
        assert response.status_code == 200

        response = await client.get(
            "/fmcg/events/stats",
            headers=_headers("admin"),
        )
        assert response.status_code == 200
        assert response.json()["total_events"] >= 2

        response = await client.get(
            f"/fmcg/events/{event['event_id']}/history",
            headers=_headers("analyst"),
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = await client.post(
            "/fmcg/events/compact",
            headers=_headers("admin"),
        )
        assert response.status_code == 200
        assert response.json()["retained_events"] >= 2

        response = await client.post(
            "/fmcg/events/archive",
            headers=_headers("admin"),
            json={"before_timestamp": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        )
        assert response.status_code == 200
        assert response.json()["archived_events"] >= 2


if __name__ == "__main__":
    asyncio.run(_run())
    print("API smoke checks passed")