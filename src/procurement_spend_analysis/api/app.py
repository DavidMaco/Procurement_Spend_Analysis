from __future__ import annotations

import time
import uuid

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from dashboard_data import build_bundle_from_upload_bytes, generate_demo_bundle
from procurement_spend_analysis.config import get_settings
from procurement_spend_analysis.fmcg.api_router import router as fmcg_router
from procurement_spend_analysis.api.saas_router import router as saas_router
from procurement_spend_analysis.ml.models import detect_procurement_anomalies, forecast_category_demand
from procurement_spend_analysis.observability import (
    METRICS_CONTENT_TYPE,
    configure_logging,
    get_logger,
    metrics_payload,
    record_request_metrics,
)
from procurement_spend_analysis.security import sanitize_filename, validate_text_payload


settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(title="Procurement Intelligence SaaS API", version=settings.package_version)
app.include_router(fmcg_router)
app.include_router(saas_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class DemoRequest(BaseModel):
    num_orders: int = 2500
    seed: int = 42
    num_quality_incidents: int = 150


@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        response = await call_next(request)
    except Exception as exc:
        duration = time.perf_counter() - start
        logger.exception("Unhandled request failure", extra={"request_id": request_id, "path": request.url.path, "duration_ms": round(duration * 1000, 2)})
        record_request_metrics(request.method, request.url.path, 500, duration)
        raise exc
    duration = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    record_request_metrics(request.method, request.url.path, response.status_code, duration)
    logger.info(
        "Request handled",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "environment": settings.environment,
        },
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_payload(), media_type=METRICS_CONTENT_TYPE)


@app.post("/analytics/demo")
def analytics_demo(payload: DemoRequest) -> dict:
    bundle = generate_demo_bundle(
        num_orders=payload.num_orders,
        seed=payload.seed,
        num_quality_incidents=payload.num_quality_incidents,
    )
    return {
        "metadata": bundle["metadata"],
        "insights": bundle["insights"],
        "summary": bundle["analytics"]["procurement_insights_summary"].to_dict(orient="records"),
    }


@app.post("/analytics/upload")
async def analytics_upload(files: list[UploadFile] = File(...)) -> dict:
    uploaded: dict[str, bytes] = {}
    for file in files:
        safe_name = sanitize_filename(file.filename or "upload.csv")
        payload = await file.read()
        validate_text_payload(payload.decode("utf-8", errors="ignore"), max_chars=settings.max_upload_file_size_mb * 1024 * 1024)
        uploaded[safe_name] = payload
    try:
        bundle = build_bundle_from_upload_bytes(uploaded)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"metadata": bundle["metadata"], "insights": bundle["insights"]}


@app.post("/ml/forecast")
def ml_forecast(payload: DemoRequest) -> dict:
    bundle = generate_demo_bundle(payload.num_orders, payload.seed, payload.num_quality_incidents)
    forecast = forecast_category_demand(bundle["raw"]["purchase_orders"])
    return {"forecast": forecast.to_dict(orient="records")}


@app.post("/ml/anomalies")
def ml_anomalies(payload: DemoRequest) -> dict:
    bundle = generate_demo_bundle(payload.num_orders, payload.seed, payload.num_quality_incidents)
    anomalies = detect_procurement_anomalies(bundle["raw"]["purchase_orders"])
    flagged = anomalies[anomalies["is_anomaly"]].head(25)
    return {"anomalies": flagged.to_dict(orient="records")}


@app.exception_handler(ValueError)
def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})