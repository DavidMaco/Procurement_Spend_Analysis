import asyncio
import logging
import os
import uuid
from io import BytesIO

import httpx
import pandas as pd

if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "x" * 64

from procurement_spend_analysis.api.app import app


logging.disable(logging.CRITICAL)


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    async def _run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(_run())


def _headers(*roles: str, user_id: str = "demo-user") -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Roles": ",".join(roles)}


def _saas_auth_headers() -> dict[str, str]:
    slug = f"tenant-{uuid.uuid4().hex[:8]}"
    tenant_response = _request(
        "POST",
        "/v1/tenants",
        json={
            "name": "Test Tenant",
            "slug": slug,
            "owner_email": f"{slug}@example.com",
            "tier": "professional",
        },
    )
    assert tenant_response.status_code == 201
    tenant_id = tenant_response.json()["tenant_id"]

    token_response = _request(
        "POST",
        "/v1/auth/token",
        json={"user_id": "user-1", "tenant_id": tenant_id, "roles": ["admin"]},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def _make_pilot_upload() -> BytesIO:
    rows: list[dict[str, object]] = []
    dates = ["1/1/2021", "1/2/2021", "1/3/2021", "1/4/2021"]
    stores = ["STORE001", "STORE002", "STORE003", "STORE004"]
    for day_index, day in enumerate(dates, start=1):
        for store in stores:
            is_treatment = store in {"STORE003", "STORE004"}
            post_period = day_index >= 3
            discount_pct = 0.5
            purchase_cost = 6.0
            if is_treatment and post_period:
                discount_pct = 0.4
                purchase_cost = 5.0

            gross_sales = 200.0
            net_sales = gross_sales * (1 - discount_pct)
            margin_pct = (net_sales - (purchase_cost * 10)) / net_sales
            rows.append(
                {
                    "date": day,
                    "year": 2021,
                    "month": 1,
                    "day": day_index,
                    "weekofyear": 1,
                    "weekday": (day_index + 3) % 7,
                    "is_weekend": 1 if day_index in {2, 3} else 0,
                    "is_holiday": 0,
                    "temperature": 25.0,
                    "rain_mm": 0.0,
                    "store_id": store,
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
                    "list_price": 20.0,
                    "discount_pct": discount_pct,
                    "promo_flag": 1,
                    "gross_sales": gross_sales,
                    "net_sales": net_sales,
                    "stock_on_hand": 25,
                    "stock_out_flag": 0,
                    "lead_time_days": 5,
                    "supplier_id": "S001",
                    "purchase_cost": purchase_cost,
                    "margin_pct": round(margin_pct, 3),
                }
            )
    return BytesIO(pd.DataFrame(rows).to_csv(index=False).encode("utf-8"))


def test_health_endpoint_returns_ok():
    response = _request("GET", "/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint_responds():
    response = _request("GET", "/metrics")
    assert response.status_code == 200
    assert (
        b"procurement_api_requests_total" in response.content or response.content == b""
    )


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
    assert any(
        alert["rule_name"] == "gross_to_net_leakage_spike"
        for alert in payload["alerts"]
    )


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


def test_fmcg_pilot_evaluation_returns_incremental_lift():
    upload = _make_pilot_upload()
    response = _request(
        "POST",
        "/fmcg/pilot/evaluate?intervention_date=2021-01-03",
        headers=_headers("analyst"),
        files={"file": ("pilot.csv", upload, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["primary_metric"] == "net_sales_per_store_day"
    assert payload["primary_incremental_lift"] > 0
    assert payload["cohort"]["control_stores"] == ["STORE001", "STORE002"]
    assert payload["cohort"]["treatment_stores"] == ["STORE003", "STORE004"]
    net_sales_impact = next(
        impact
        for impact in payload["metric_impacts"]
        if impact["metric"] == "net_sales_per_store_day"
    )
    assert net_sales_impact["incremental_lift"] == 20.0
    assert net_sales_impact["favorable_movement"] is True


def test_fmcg_event_stats_include_integrity_fields():
    create_response = _request(
        "POST",
        "/fmcg/events/recommendations",
        headers=_headers("analyst"),
        json={
            "model_id": "promo_v3",
            "model_version": "2.2.0",
            "input_snapshot_ref": "s3://bucket/snap_003.parquet",
            "recommendation_type": "supplier_switch",
            "recommendation_payload": {
                "supplier_id": "SUP-1",
                "target_supplier_id": "SUP-2",
            },
            "confidence_score": 0.84,
        },
    )
    assert create_response.status_code == 200

    response = _request("GET", "/fmcg/events/stats", headers=_headers("admin"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["integrity_verified"] is True
    assert len(payload["chain_head"]) == 64


def test_fmcg_event_integrity_endpoint_returns_recent_links():
    create_response = _request(
        "POST",
        "/fmcg/events/recommendations",
        headers=_headers("analyst"),
        json={
            "model_id": "promo_v4",
            "model_version": "2.3.0",
            "input_snapshot_ref": "s3://bucket/snap_004.parquet",
            "recommendation_type": "promo_depth",
            "recommendation_payload": {"sku": "SKU-9", "discount": 0.15},
            "confidence_score": 0.88,
        },
    )
    assert create_response.status_code == 200

    response = _request(
        "GET",
        "/fmcg/events/integrity?limit=5",
        headers=_headers("admin"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["integrity_verified"] is True
    assert payload["checked_events"] >= 1
    assert payload["broken_links"] == 0
    assert len(payload["rows"]) >= 1
    assert payload["rows"][-1]["link_ok"] is True


def test_saas_intelligence_summary_includes_forecasts():
    response = _request("GET", "/v1/intelligence/summary", headers=_saas_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert "forecasts" in payload
    assert isinstance(payload["forecasts"], list)
    assert len(payload["forecasts"]) > 0


def test_saas_forecast_endpoint_returns_forecasts():
    response = _request(
        "GET", "/v1/intelligence/forecast", headers=_saas_auth_headers()
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] > 0
    assert len(payload["forecasts"]) == payload["count"]
