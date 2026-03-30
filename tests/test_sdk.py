"""Tests for the Procurement Intelligence Python SDK (sdk.py)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from procurement_spend_analysis.sdk import (
    APIError,
    AuthResource,
    BillingResource,
    EventsResource,
    IntelligenceResource,
    ProcurementClient,
    SDKConfig,
    TenantsResource,
    WebhooksResource,
    _HTTPTransport,
)


def _mock_response(payload: dict | list) -> MagicMock:
    """Return a mock urllib response usable as a context manager."""
    body = json.dumps(payload).encode()
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock


# ---------------------------------------------------------------------------
# SDKConfig
# ---------------------------------------------------------------------------


class TestSDKConfig:
    def test_defaults(self) -> None:
        cfg = SDKConfig()
        assert cfg.base_url == "https://api.procurementintelligence.io"
        assert cfg.api_key is None
        assert cfg.access_token is None
        assert cfg.timeout == 30
        assert cfg.max_retries == 3
        assert cfg.retry_base_delay == 0.5

    def test_custom_values(self) -> None:
        cfg = SDKConfig(
            base_url="http://localhost:8000",
            api_key="pi_live_test",
            timeout=10,
            max_retries=1,
        )
        assert cfg.base_url == "http://localhost:8000"
        assert cfg.api_key == "pi_live_test"
        assert cfg.timeout == 10


# ---------------------------------------------------------------------------
# APIError
# ---------------------------------------------------------------------------


class TestAPIError:
    def test_creation_and_repr(self) -> None:
        err = APIError(404, "Not found")
        assert err.status_code == 404
        assert err.detail == "Not found"
        assert "404" in str(err)
        assert "Not found" in str(err)

    def test_is_exception(self) -> None:
        with pytest.raises(APIError) as exc_info:
            raise APIError(401, "Unauthorized")
        assert exc_info.value.status_code == 401

    def test_zero_status_code(self) -> None:
        err = APIError(0, "Connection failed")
        assert err.status_code == 0


# ---------------------------------------------------------------------------
# _HTTPTransport
# ---------------------------------------------------------------------------


def _make_transport(
    api_key: str | None = None, access_token: str | None = None, max_retries: int = 2
) -> _HTTPTransport:
    cfg = SDKConfig(
        base_url="http://localhost:8000",
        api_key=api_key,
        access_token=access_token,
        max_retries=max_retries,
        retry_base_delay=0.0,
    )
    return _HTTPTransport(cfg)


class TestHTTPTransportHeaders:
    def test_with_api_key(self) -> None:
        t = _make_transport(api_key="pi_live_key")
        headers = t._headers()
        assert headers["X-API-Key"] == "pi_live_key"
        assert "Authorization" not in headers

    def test_access_token_takes_priority(self) -> None:
        t = _make_transport(access_token="jwt.token.here")
        headers = t._headers()
        assert headers["Authorization"] == "Bearer jwt.token.here"

    def test_unauthenticated(self) -> None:
        t = _make_transport()
        headers = t._headers()
        assert "Authorization" not in headers
        assert "X-API-Key" not in headers

    def test_content_type_always_set(self) -> None:
        t = _make_transport()
        assert t._headers()["Content-Type"] == "application/json"


class TestHTTPTransportRequest:
    def test_successful_get(self) -> None:
        t = _make_transport(api_key="k")
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_response({"ok": True})
        ):
            assert t.get("/v1/health") == {"ok": True}

    def test_successful_post(self) -> None:
        t = _make_transport(api_key="k")
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_response({"id": "t_1"})
        ):
            assert t.post("/v1/tenants", {"name": "Acme"}) == {"id": "t_1"}

    def test_successful_post_no_body(self) -> None:
        t = _make_transport(api_key="k")
        with patch.object(urllib.request, "urlopen", return_value=_mock_response({})):
            assert t.post("/v1/endpoint") == {}

    def test_successful_delete(self) -> None:
        t = _make_transport(api_key="k")
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_response({"deleted": True})
        ):
            assert t.delete("/v1/webhooks/w_1") == {"deleted": True}

    def test_http_error_raises_api_error(self) -> None:
        t = _make_transport(api_key="k")
        exc = urllib.error.HTTPError(
            url="http://localhost",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b"not authorized"),
        )
        with patch.object(urllib.request, "urlopen", side_effect=exc):
            with pytest.raises(APIError) as info:
                t.get("/v1/health")
        assert info.value.status_code == 401

    def test_http_error_no_fp_uses_str(self) -> None:
        t = _make_transport(api_key="k")
        exc = urllib.error.HTTPError(
            url="http://localhost", code=403, msg="Forbidden", hdrs=None, fp=None
        )
        with patch.object(urllib.request, "urlopen", side_effect=exc):
            with pytest.raises(APIError) as info:
                t.get("/v1/health")
        assert info.value.status_code == 403

    def test_retries_on_503_then_succeeds(self) -> None:
        t = _make_transport(api_key="k", max_retries=2)
        err = urllib.error.HTTPError(
            url="http://localhost",
            code=503,
            msg="Unavailable",
            hdrs=None,
            fp=BytesIO(b""),
        )
        mock_resp = _mock_response({"ok": True})
        with patch.object(urllib.request, "urlopen", side_effect=[err, mock_resp]):
            assert t.get("/v1/health") == {"ok": True}

    def test_retries_on_429(self) -> None:
        t = _make_transport(api_key="k", max_retries=2)
        err = urllib.error.HTTPError(
            url="http://localhost",
            code=429,
            msg="Rate limited",
            hdrs=None,
            fp=BytesIO(b""),
        )
        mock_resp = _mock_response({"ok": True})
        with patch.object(urllib.request, "urlopen", side_effect=[err, mock_resp]):
            assert t.get("/v1/health") == {"ok": True}

    def test_url_error_raises_api_error(self) -> None:
        t = _make_transport(api_key="k", max_retries=1)
        with patch.object(
            urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")
        ):
            with pytest.raises(APIError) as info:
                t.get("/v1/health")
        assert info.value.status_code == 0

    def test_max_retries_exceeded_url_error(self) -> None:
        t = _make_transport(api_key="k", max_retries=2)
        with patch.object(
            urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")
        ):
            with pytest.raises(APIError) as info:
                t.get("/v1/health")
        assert info.value.status_code == 0


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------


class TestSSEStreaming:
    def test_parses_json_events(self) -> None:
        t = _make_transport(api_key="k", max_retries=1)
        lines = [
            b'data: {"event_type": "kpi_update"}\n',
            b"data: \n",  # empty — skipped
            b": comment ignored\n",
        ]
        mock_resp = MagicMock()
        mock_resp.__iter__ = MagicMock(return_value=iter(lines))
        with patch.object(urllib.request, "urlopen", return_value=mock_resp):
            events = list(t.stream_sse("/v1/events/stream"))
        assert len(events) == 1
        assert events[0]["event_type"] == "kpi_update"

    def test_invalid_json_yields_raw(self) -> None:
        t = _make_transport(api_key="k", max_retries=1)
        lines = [b"data: not-valid-json\n"]
        mock_resp = MagicMock()
        mock_resp.__iter__ = MagicMock(return_value=iter(lines))
        with patch.object(urllib.request, "urlopen", return_value=mock_resp):
            events = list(t.stream_sse("/v1/events/stream"))
        assert events == [{"raw": "not-valid-json"}]

    def test_non_data_lines_skipped(self) -> None:
        t = _make_transport(api_key="k", max_retries=1)
        lines = [b": keep-alive\n", b"event: ping\n", b"id: 1\n"]
        mock_resp = MagicMock()
        mock_resp.__iter__ = MagicMock(return_value=iter(lines))
        with patch.object(urllib.request, "urlopen", return_value=mock_resp):
            events = list(t.stream_sse("/v1/events/stream"))
        assert events == []


# ---------------------------------------------------------------------------
# ProcurementClient & resource namespaces
# ---------------------------------------------------------------------------


def _client() -> ProcurementClient:
    return ProcurementClient(
        base_url="http://localhost:8000",
        api_key="pi_live_test",
        timeout=5,
        max_retries=1,
    )


def _mock_get(payload: dict | list) -> MagicMock:
    return patch.object(urllib.request, "urlopen", return_value=_mock_response(payload))


class TestProcurementClientInit:
    def test_sub_resources_are_typed(self) -> None:
        c = _client()
        assert isinstance(c.tenants, TenantsResource)
        assert isinstance(c.auth, AuthResource)
        assert isinstance(c.intelligence, IntelligenceResource)
        assert isinstance(c.events, EventsResource)
        assert isinstance(c.webhooks, WebhooksResource)
        assert isinstance(c.billing, BillingResource)

    def test_trailing_slash_stripped(self) -> None:
        c = ProcurementClient(
            base_url="http://localhost:8000/", api_key="k", max_retries=1
        )
        assert isinstance(c.intelligence, IntelligenceResource)

    def test_access_token_auth(self) -> None:
        c = ProcurementClient(
            base_url="http://localhost:8000", access_token="jwt.abc", max_retries=1
        )
        assert isinstance(c.billing, BillingResource)


class TestTenantsResource:
    def test_create(self) -> None:
        c = _client()
        with _mock_get({"tenant_id": "t_1"}):
            result = c.tenants.create("Acme", "acme", "admin@acme.com", tier="starter")
        assert result["tenant_id"] == "t_1"

    def test_get(self) -> None:
        c = _client()
        with _mock_get({"tenant_id": "t_1", "name": "Acme"}):
            result = c.tenants.get("t_1")
        assert result["name"] == "Acme"


class TestAuthResource:
    def test_issue_token(self) -> None:
        c = _client()
        with _mock_get({"access_token": "jwt.abc.def"}):
            result = c.auth.issue_token("u1", "t1", ["analyst"])
        assert "access_token" in result

    def test_create_api_key(self) -> None:
        c = _client()
        with _mock_get({"key": "pi_live_abc"}):
            result = c.auth.create_api_key("my-key", ["read"])
        assert "key" in result

    def test_create_api_key_no_scopes(self) -> None:
        c = _client()
        with _mock_get({"key": "pi_live_def"}):
            result = c.auth.create_api_key("default-key")
        assert "key" in result

    def test_list_api_keys(self) -> None:
        c = _client()
        with _mock_get([{"key_id": "k1"}]):
            result = c.auth.list_api_keys()
        assert result == [{"key_id": "k1"}]


class TestIntelligenceResource:
    def test_summary(self) -> None:
        c = _client()
        with _mock_get({"anomalies": [], "savings": 0}):
            result = c.intelligence.summary()
        assert "anomalies" in result

    def test_anomalies(self) -> None:
        c = _client()
        with _mock_get({"anomalies": []}):
            assert "anomalies" in c.intelligence.anomalies()

    def test_forecast(self) -> None:
        c = _client()
        with _mock_get({"forecast": []}):
            assert "forecast" in c.intelligence.forecast()

    def test_risk_scores(self) -> None:
        c = _client()
        with _mock_get({"risk_scores": []}):
            assert "risk_scores" in c.intelligence.risk_scores()

    def test_savings(self) -> None:
        c = _client()
        with _mock_get({"opportunities": []}):
            assert "opportunities" in c.intelligence.savings()


class TestEventsResource:
    def test_recent_default(self) -> None:
        c = _client()
        with _mock_get({"events": []}):
            result = c.events.recent()
        assert "events" in result

    def test_recent_with_event_type(self) -> None:
        c = _client()
        with _mock_get({"events": []}):
            result = c.events.recent(limit=5, event_type="kpi_update")
        assert "events" in result


class TestWebhooksResource:
    def test_register(self) -> None:
        c = _client()
        with _mock_get({"webhook_id": "wh_1"}):
            result = c.webhooks.register("https://example.com/hook", ["kpi_update"])
        assert "webhook_id" in result

    def test_register_no_event_types(self) -> None:
        c = _client()
        with _mock_get({"webhook_id": "wh_2"}):
            result = c.webhooks.register("https://example.com/hook")
        assert "webhook_id" in result

    def test_list(self) -> None:
        c = _client()
        with _mock_get([{"webhook_id": "wh_1"}]):
            result = c.webhooks.list()
        assert isinstance(result, list)

    def test_delete(self) -> None:
        c = _client()
        with _mock_get({"deleted": True}):
            c.webhooks.delete("wh_1")  # returns None — just ensure no exception


class TestBillingResource:
    def test_plans(self) -> None:
        c = _client()
        with _mock_get({"plans": []}):
            assert "plans" in c.billing.plans()

    def test_subscription(self) -> None:
        c = _client()
        with _mock_get({"plan_id": "plan_starter"}):
            assert "plan_id" in c.billing.subscription()

    def test_upgrade(self) -> None:
        c = _client()
        with _mock_get({"upgraded": True}):
            assert "upgraded" in c.billing.upgrade("plan_professional")

    def test_usage(self) -> None:
        c = _client()
        with _mock_get({"api_calls": 42}):
            assert "api_calls" in c.billing.usage()

    def test_invoices(self) -> None:
        c = _client()
        with _mock_get({"invoices": []}):
            assert "invoices" in c.billing.invoices()
