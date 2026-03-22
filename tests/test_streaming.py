"""Tests for real-time streaming, event bus, SSE, and webhooks (streaming.py)."""

from __future__ import annotations


from procurement_spend_analysis.streaming import (
    EventBus,
    EventType,
    SSEManager,
    StreamEvent,
    WebhookService,
    WebhookStatus,
    get_event_bus,
    get_sse_manager,
    get_webhook_service,
)


# ── EventBus ─────────────────────────────────────────────────────────────


class TestEventBus:
    def test_publish_and_recent(self):
        bus = EventBus()
        event = StreamEvent(
            event_type=EventType.ALERT_FIRED.value,
            tenant_id="t1",
            payload={"msg": "test"},
            source="test",
        )
        bus.publish(event)
        recent = bus.recent_events(limit=10)
        assert len(recent) == 1
        assert recent[0].event_type == EventType.ALERT_FIRED.value

    def test_subscribe_callback(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.ANOMALY_DETECTED.value, lambda e: received.append(e))
        event = StreamEvent(
            event_type=EventType.ANOMALY_DETECTED.value,
            tenant_id="t1",
            payload={},
            source="test",
        )
        bus.publish(event)
        assert len(received) == 1

    def test_subscribe_all(self):
        bus = EventBus()
        received = []
        bus.subscribe_all(lambda e: received.append(e))
        for etype in [EventType.ALERT_FIRED.value, EventType.FORECAST_READY.value]:
            bus.publish(
                StreamEvent(event_type=etype, tenant_id="t1", payload={}, source="test")
            )
        assert len(received) == 2

    def test_filter_by_event_type(self):
        bus = EventBus()
        bus.publish(
            StreamEvent(event_type="a", tenant_id="t1", payload={}, source="test")
        )
        bus.publish(
            StreamEvent(event_type="b", tenant_id="t1", payload={}, source="test")
        )
        assert len(bus.recent_events(event_type="a")) == 1

    def test_filter_by_tenant(self):
        bus = EventBus()
        bus.publish(
            StreamEvent(event_type="a", tenant_id="t1", payload={}, source="test")
        )
        bus.publish(
            StreamEvent(event_type="a", tenant_id="t2", payload={}, source="test")
        )
        assert len(bus.recent_events(tenant_id="t1")) == 1


# ── SSEManager ───────────────────────────────────────────────────────────


class TestSSEManager:
    def test_get_channel(self):
        mgr = SSEManager()
        ch = mgr.get_channel("t1")
        assert ch.client_count == 0

    def test_broadcast_to_channel(self):
        mgr = SSEManager()
        ch = mgr.get_channel("t1")
        q = ch.connect()
        event = StreamEvent(
            event_type="test", tenant_id="t1", payload={}, source="test"
        )
        ch.broadcast(event)
        # Queue should have the event
        assert not q.empty()
        ch.disconnect(q)


# ── WebhookService ───────────────────────────────────────────────────────


class TestWebhookService:
    def test_register_webhook(self):
        svc = WebhookService()
        ep = svc.register(
            tenant_id="t1",
            url="https://example.com/webhook",
            event_types=[EventType.ALERT_FIRED.value],
        )
        assert ep.tenant_id == "t1"
        assert ep.status == WebhookStatus.ACTIVE

    def test_list_for_tenant(self):
        svc = WebhookService()
        svc.register(tenant_id="t1", url="https://a.com/hook")
        svc.register(tenant_id="t1", url="https://b.com/hook")
        svc.register(tenant_id="t2", url="https://c.com/hook")
        assert len(svc.list_for_tenant("t1")) == 2
        assert len(svc.list_for_tenant("t2")) == 1

    def test_delete_webhook(self):
        svc = WebhookService()
        ep = svc.register(tenant_id="t1", url="https://a.com/hook")
        svc.delete(ep.webhook_id)
        assert len(svc.list_for_tenant("t1")) == 0

    def test_sign_payload(self):
        svc = WebhookService()
        sig = svc.sign_payload("secret123", '{"event": "test"}')
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest

    def test_matching_endpoints(self):
        svc = WebhookService()
        svc.register(
            tenant_id="t1", url="https://a.com/hook", event_types=["alert.fired"]
        )
        svc.register(
            tenant_id="t1", url="https://b.com/hook", event_types=["forecast.ready"]
        )
        event = StreamEvent(
            event_type="alert.fired", tenant_id="t1", payload={}, source="test"
        )
        matches = svc.matching_endpoints(event)
        assert len(matches) == 1
        assert matches[0].url == "https://a.com/hook"

    def test_record_delivery(self):
        svc = WebhookService()
        ep = svc.register(tenant_id="t1", url="https://a.com/hook")
        delivery = svc.record_delivery(
            webhook_id=ep.webhook_id,
            event_id="ev1",
            status_code=200,
            success=True,
            response_time_ms=50.0,
        )
        assert delivery.success is True
        history = svc.delivery_history(webhook_id=ep.webhook_id)
        assert len(history) == 1


# ── Singletons ───────────────────────────────────────────────────────────


class TestSingletons:
    def test_event_bus_singleton(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_sse_manager_singleton(self):
        mgr1 = get_sse_manager()
        mgr2 = get_sse_manager()
        assert mgr1 is mgr2

    def test_webhook_service_singleton(self):
        svc1 = get_webhook_service()
        svc2 = get_webhook_service()
        assert svc1 is svc2
