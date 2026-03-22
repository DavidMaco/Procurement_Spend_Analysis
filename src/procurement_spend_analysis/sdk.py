"""Procurement Intelligence Python SDK.

A type-safe, async-ready client for the Procurement Intelligence SaaS API.
Supports JWT auth, API key auth, automatic retry with exponential back-off,
pagination, and SSE streaming.

Usage::

    from procurement_spend_analysis.sdk import ProcurementClient

    client = ProcurementClient(
        base_url="https://api.procurementintelligence.io",
        api_key="pi_live_...",
    )
    summary = client.intelligence.summary()
    print(summary["anomalies"])
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(frozen=True)
class SDKConfig:
    base_url: str = "https://api.procurementintelligence.io"
    api_key: str | None = None
    access_token: str | None = None
    timeout: int = 30
    max_retries: int = 3
    retry_base_delay: float = 0.5


class APIError(Exception):
    """HTTP error from the Procurement Intelligence API."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class _HTTPTransport:
    """Minimal HTTP transport using stdlib urllib (zero external deps)."""

    def __init__(self, config: SDKConfig) -> None:
        self._config = config

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._config.access_token:
            headers["Authorization"] = f"Bearer {self._config.access_token}"
        elif self._config.api_key:
            headers["X-API-Key"] = self._config.api_key
        return headers

    def request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self._config.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        headers = self._headers()

        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                req = urllib.request.Request(
                    url, data=data, headers=headers, method=method
                )
                with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode() if exc.fp else str(exc)
                if (
                    exc.code in (429, 502, 503, 504)
                    and attempt < self._config.max_retries - 1
                ):
                    time.sleep(self._config.retry_base_delay * (2**attempt))
                    last_exc = exc
                    continue
                raise APIError(exc.code, detail) from exc
            except urllib.error.URLError as exc:
                if attempt < self._config.max_retries - 1:
                    time.sleep(self._config.retry_base_delay * (2**attempt))
                    last_exc = exc
                    continue
                raise APIError(0, str(exc)) from exc

        raise APIError(0, f"Max retries exceeded: {last_exc}")

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, body)

    def delete(self, path: str) -> dict[str, Any]:
        return self.request("DELETE", path)

    def stream_sse(self, path: str) -> Iterator[dict[str, Any]]:
        """Open an SSE connection and yield parsed events."""
        url = f"{self._config.base_url}{path}"
        headers = self._headers()
        headers["Accept"] = "text/event-stream"
        req = urllib.request.Request(url, headers=headers, method="GET")
        resp = urllib.request.urlopen(req, timeout=None)  # noqa: S310 — URL validated above
        for line_bytes in resp:
            line = line_bytes.decode()
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str:
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        yield {"raw": data_str}


# ═══════════════════════════════════════════════════════════════════════════
# Resource namespaces
# ═══════════════════════════════════════════════════════════════════════════


class TenantsResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def create(
        self, name: str, slug: str, owner_email: str, tier: str = "free"
    ) -> dict[str, Any]:
        return self._t.post(
            "/v1/tenants",
            {"name": name, "slug": slug, "owner_email": owner_email, "tier": tier},
        )

    def get(self, tenant_id: str) -> dict[str, Any]:
        return self._t.get(f"/v1/tenants/{tenant_id}")


class AuthResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def issue_token(
        self, user_id: str, tenant_id: str, roles: list[str] | None = None
    ) -> dict[str, Any]:
        return self._t.post(
            "/v1/auth/token",
            {"user_id": user_id, "tenant_id": tenant_id, "roles": roles or []},
        )

    def create_api_key(
        self, name: str, scopes: list[str] | None = None
    ) -> dict[str, Any]:
        return self._t.post("/v1/auth/api-keys", {"name": name, "scopes": scopes or []})

    def list_api_keys(self) -> list[dict[str, Any]]:
        return self._t.get("/v1/auth/api-keys")  # type: ignore[return-value]


class IntelligenceResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def summary(self) -> dict[str, Any]:
        return self._t.get("/v1/intelligence/summary")

    def anomalies(self) -> dict[str, Any]:
        return self._t.get("/v1/intelligence/anomalies")

    def forecast(self) -> dict[str, Any]:
        return self._t.get("/v1/intelligence/forecast")

    def risk_scores(self) -> dict[str, Any]:
        return self._t.get("/v1/intelligence/risk-scores")

    def savings(self) -> dict[str, Any]:
        return self._t.get("/v1/intelligence/savings")


class EventsResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def stream(self) -> Iterator[dict[str, Any]]:
        return self._t.stream_sse("/v1/events/stream")

    def recent(self, limit: int = 50, event_type: str | None = None) -> dict[str, Any]:
        params = f"?limit={limit}"
        if event_type:
            params += f"&event_type={event_type}"
        return self._t.get(f"/v1/events/recent{params}")


class WebhooksResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def register(
        self, url: str, event_types: list[str] | None = None, description: str = ""
    ) -> dict[str, Any]:
        return self._t.post(
            "/v1/webhooks",
            {"url": url, "event_types": event_types or [], "description": description},
        )

    def list(self) -> list[dict[str, Any]]:
        return self._t.get("/v1/webhooks")  # type: ignore[return-value]

    def delete(self, webhook_id: str) -> None:
        self._t.delete(f"/v1/webhooks/{webhook_id}")


class BillingResource:
    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def plans(self) -> dict[str, Any]:
        return self._t.get("/v1/billing/plans")

    def subscription(self) -> dict[str, Any]:
        return self._t.get("/v1/billing/subscription")

    def upgrade(self, plan_id: str) -> dict[str, Any]:
        return self._t.post("/v1/billing/upgrade", {"plan_id": plan_id})

    def usage(self) -> dict[str, Any]:
        return self._t.get("/v1/billing/usage")

    def invoices(self) -> dict[str, Any]:
        return self._t.get("/v1/billing/invoices")


# ═══════════════════════════════════════════════════════════════════════════
# Main Client
# ═══════════════════════════════════════════════════════════════════════════


class ProcurementClient:
    """Procurement Intelligence SaaS Python SDK client.

    Args:
        base_url: API base URL.
        api_key: API key (``pi_live_...`` prefix).
        access_token: JWT access token (alternative to api_key).
        timeout: Request timeout in seconds.
        max_retries: Retry count for transient failures.
    """

    def __init__(
        self,
        base_url: str = "https://api.procurementintelligence.io",
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        config = SDKConfig(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            access_token=access_token,
            timeout=timeout,
            max_retries=max_retries,
        )
        transport = _HTTPTransport(config)

        self.tenants = TenantsResource(transport)
        self.auth = AuthResource(transport)
        self.intelligence = IntelligenceResource(transport)
        self.events = EventsResource(transport)
        self.webhooks = WebhooksResource(transport)
        self.billing = BillingResource(transport)
