from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


REQUEST_COUNT = Counter("procurement_api_requests_total", "Total API requests", ["method", "path", "status_code"])
REQUEST_LATENCY = Histogram("procurement_api_request_latency_seconds", "API request latency", ["method", "path"])

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST


def record_request_metrics(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status_code=str(status_code)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)


def metrics_payload() -> bytes:
    return generate_latest()
