import asyncio
import logging
from io import BytesIO

import httpx
import pandas as pd

from procurement_spend_analysis.api.app import app


logging.disable(logging.CRITICAL)


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    async def _run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(_run())


def _headers(*roles: str, user_id: str = "demo-user") -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Roles": ",".join(roles)}


def _make_fmcg_upload(*, discount_pct: float, net_multiplier: float = 1.0) -> BytesIO:
    gross_sales = 100.0
    net_sales = gross_sales * (1 - discount_pct) * net_multiplier
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
                "margin_pct": round((net_sales - 60.0) / net_sales, 3),
            }
        ]
    )
    return BytesIO(df.to_csv(index=False).encode("utf-8"))


def test_health_endpoint_returns_ok():
    response = _request("GET", "/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint_responds():
    response = _request("GET", "/metrics")
    assert response.status_code == 200
    assert b"procurement_api_requests_total" in response.content or response.content == b""


def test_demo_endpoint_returns_summary_and_insights():
    response = _request(
        "POST",
        "/analytics/demo",
        json={"num_orders": 100, "seed": 7, "num_quality_incidents": 20},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "insights" in payload
    assert "summary" in payload
    assert payload["insights"]["total_spend"] > 0


def test_fmcg_metrics_requires_headers():
    response = _request("GET", "/fmcg/metrics")
    assert response.status_code == 401


def test_fmcg_metrics_allows_authorized_role():
    response = _request(
        "GET",
        "/fmcg/metrics",
        headers=_headers("analyst", user_id="analyst-1"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(metric["name"] == "gross_sales" for metric in payload)


def test_fmcg_alert_rules_visible_to_authorized_user():
    response = _request("GET", "/fmcg/alerts/rules", headers=_headers("viewer"))
    assert response.status_code == 200
    payload = response.json()
    assert any(rule["name"] == "gross_to_net_leakage_spike" for rule in payload)


def test_fmcg_alert_evaluation_returns_fired_alerts():
    baseline_file = _make_fmcg_upload(discount_pct=0.05)
    current_file = _make_fmcg_upload(discount_pct=0.30)
    response = _request(
        "POST",
        "/fmcg/alerts/evaluate",
        headers=_headers("viewer"),
        files={
            "baseline_file": ("baseline.csv", baseline_file, "text/csv"),
            "current_file": ("current.csv", current_file, "text/csv"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_count"] >= 1
    assert any(alert["rule_name"] == "gross_to_net_leakage_spike" for alert in payload["alerts"])


def test_fmcg_event_lifecycle_exposes_history():
    create_response = _request(
        "POST",
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
    assert create_response.status_code == 200
    event = create_response.json()

    approve_response = _request(
        "POST",
        f"/fmcg/events/{event['event_id']}/approve",
        headers=_headers("approver"),
        json={"approver_id": "approver-7"},
    )
    assert approve_response.status_code == 200
    approval = approve_response.json()
    assert approval["related_event_id"] == event["event_id"]

    history_response = _request(
        "GET",
        f"/fmcg/events/{event['event_id']}/history",
        headers=_headers("analyst"),
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["event_id"] == event["event_id"]
    assert history[1]["related_event_id"] == event["event_id"]
