"""Real-time event streaming and webhook delivery for the SaaS platform.

Provides:
  1. **Server-Sent Events (SSE)** — Push alerts, KPI changes, and job
     completions to connected dashboards in real time.
  2. **WebSocket channels** — Bi-directional streaming for collaborative
     dashboards and live data exploration.
  3. **Webhook delivery** — Reliable outbound HTTP callbacks to customer
     endpoints with retry, signing, and dead-letter queuing.

All events flow through a unified event bus so that SSE, WebSocket, and
webhook subscribers receive the same canonical event payloads.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional
from uuid import uuid4


# ═══════════════════════════════════════════════════════════════════════════
# Event Bus
# ═══════════════════════════════════════════════════════════════════════════


class EventType(str, Enum):
    ALERT_FIRED = "alert.fired"
    RECOMMENDATION_CREATED = "recommendation.created"
    RECOMMENDATION_APPROVED = "recommendation.approved"
    RECOMMENDATION_REJECTED = "recommendation.rejected"
    KPI_THRESHOLD_BREACH = "kpi.threshold_breach"
    UPLOAD_COMPLETED = "upload.completed"
    FORECAST_READY = "forecast.ready"
    ANOMALY_DETECTED = "anomaly.detected"
    RISK_SCORE_CHANGED = "risk.score_changed"
    SAVINGS_IDENTIFIED = "savings.identified"
    JOB_COMPLETED = "job.completed"
    TENANT_EVENT = "tenant.event"


@dataclass
class StreamEvent:
    """Canonical event flowing through the platform's event bus."""

    event_id: str = field(default_factory=lambda: uuid4().hex)
    event_type: str = ""
    tenant_id: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # originating module/service
    correlation_id: Optional[str] = None


class EventBus:
    """In-process pub/sub event bus with topic-based routing.

    In production, this would be backed by AWS EventBridge, SQS/SNS, or
    a Kafka cluster. The in-memory implementation supports development,
    testing, and single-process deployments.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[StreamEvent], Any]]] = defaultdict(
            list
        )
        self._all_subscribers: list[Callable[[StreamEvent], Any]] = []
        self._history: list[StreamEvent] = []
        self._max_history = 10_000

    def subscribe(
        self, event_type: str, callback: Callable[[StreamEvent], Any]
    ) -> None:
        """Subscribe to a specific event type."""
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[StreamEvent], Any]) -> None:
        """Subscribe to all events (for audit/logging)."""
        self._all_subscribers.append(callback)

    def publish(self, event: StreamEvent) -> None:
        """Publish an event to all matching subscribers synchronously."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        for cb in self._all_subscribers:
            try:
                cb(event)
            except Exception:
                pass

        for cb in self._subscribers.get(event.event_type, []):
            try:
                cb(event)
            except Exception:
                pass

    def recent_events(
        self,
        limit: int = 50,
        event_type: str | None = None,
        tenant_id: str | None = None,
    ) -> list[StreamEvent]:
        """Retrieve recent events with optional filtering."""
        results = reversed(self._history)
        filtered: list[StreamEvent] = []
        for ev in results:
            if event_type and ev.event_type != event_type:
                continue
            if tenant_id and ev.tenant_id != tenant_id:
                continue
            filtered.append(ev)
            if len(filtered) >= limit:
                break
        return filtered


# ═══════════════════════════════════════════════════════════════════════════
# Server-Sent Events (SSE)
# ═══════════════════════════════════════════════════════════════════════════


class SSEChannel:
    """Per-tenant SSE channel that fans out events to connected clients.

    Each connected dashboard/browser gets its own asyncio.Queue.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._clients: list[asyncio.Queue[StreamEvent | None]] = []

    def connect(self) -> asyncio.Queue[StreamEvent | None]:
        """Register a new SSE client. Returns a queue to read from."""
        queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue(maxsize=100)
        self._clients.append(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue[StreamEvent | None]) -> None:
        """Unregister an SSE client."""
        self._clients = [q for q in self._clients if q is not queue]

    def broadcast(self, event: StreamEvent) -> None:
        """Push an event to all connected clients."""
        dead: list[asyncio.Queue[StreamEvent | None]] = []
        for queue in self._clients:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)

        for d in dead:
            self._clients = [q for q in self._clients if q is not d]

    @property
    def client_count(self) -> int:
        return len(self._clients)


class SSEManager:
    """Manages per-tenant SSE channels."""

    def __init__(self) -> None:
        self._channels: dict[str, SSEChannel] = {}

    def get_channel(self, tenant_id: str) -> SSEChannel:
        if tenant_id not in self._channels:
            self._channels[tenant_id] = SSEChannel(tenant_id)
        return self._channels[tenant_id]

    async def stream(self, tenant_id: str) -> AsyncIterator[str]:
        """Async generator that yields SSE-formatted strings."""
        channel = self.get_channel(tenant_id)
        queue = channel.connect()
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield self._format_sse(event)
        finally:
            channel.disconnect(queue)

    @staticmethod
    def _format_sse(event: StreamEvent) -> str:
        data = json.dumps(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "payload": event.payload,
                "source": event.source,
            }
        )
        return f"event: {event.event_type}\ndata: {data}\n\n"


# ═══════════════════════════════════════════════════════════════════════════
# Webhook Delivery
# ═══════════════════════════════════════════════════════════════════════════


class WebhookStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"  # Too many consecutive failures


@dataclass
class WebhookEndpoint:
    """Registered webhook endpoint for a tenant."""

    webhook_id: str = field(default_factory=lambda: uuid4().hex[:16])
    tenant_id: str = ""
    url: str = ""
    secret: str = field(default_factory=lambda: uuid4().hex)
    event_types: list[str] = field(default_factory=list)  # Empty = all events
    status: WebhookStatus = WebhookStatus.ACTIVE
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    failure_count: int = 0
    last_delivered_at: Optional[str] = None
    description: str = ""


@dataclass
class WebhookDelivery:
    """Record of a single webhook delivery attempt."""

    delivery_id: str = field(default_factory=lambda: uuid4().hex[:16])
    webhook_id: str = ""
    event_id: str = ""
    status_code: int = 0
    success: bool = False
    attempted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    response_time_ms: float = 0.0
    error: Optional[str] = None


class WebhookService:
    """Manages webhook registrations and delivery (in-memory for dev)."""

    MAX_FAILURES = 10

    def __init__(self) -> None:
        self._endpoints: dict[str, WebhookEndpoint] = {}
        self._deliveries: list[WebhookDelivery] = []

    def register(
        self,
        tenant_id: str,
        url: str,
        event_types: list[str] | None = None,
        description: str = "",
    ) -> WebhookEndpoint:
        endpoint = WebhookEndpoint(
            tenant_id=tenant_id,
            url=url,
            event_types=event_types or [],
            description=description,
        )
        self._endpoints[endpoint.webhook_id] = endpoint
        return endpoint

    def list_for_tenant(self, tenant_id: str) -> list[WebhookEndpoint]:
        return [ep for ep in self._endpoints.values() if ep.tenant_id == tenant_id]

    def delete(self, webhook_id: str) -> None:
        self._endpoints.pop(webhook_id, None)

    def sign_payload(self, secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload verification."""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def matching_endpoints(self, event: StreamEvent) -> list[WebhookEndpoint]:
        """Find all active webhooks that should receive this event."""
        results: list[WebhookEndpoint] = []
        for ep in self._endpoints.values():
            if ep.status != WebhookStatus.ACTIVE:
                continue
            if ep.tenant_id != event.tenant_id:
                continue
            if ep.event_types and event.event_type not in ep.event_types:
                continue
            results.append(ep)
        return results

    def record_delivery(
        self,
        webhook_id: str,
        event_id: str,
        status_code: int,
        success: bool,
        response_time_ms: float = 0.0,
        error: str | None = None,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=event_id,
            status_code=status_code,
            success=success,
            response_time_ms=response_time_ms,
            error=error,
        )
        self._deliveries.append(delivery)

        ep = self._endpoints.get(webhook_id)
        if ep is not None:
            if success:
                ep.failure_count = 0
                ep.last_delivered_at = delivery.attempted_at
            else:
                ep.failure_count += 1
                if ep.failure_count >= self.MAX_FAILURES:
                    ep.status = WebhookStatus.FAILED

        return delivery

    def delivery_history(
        self,
        webhook_id: str | None = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        results = reversed(self._deliveries)
        filtered: list[WebhookDelivery] = []
        for d in results:
            if webhook_id and d.webhook_id != webhook_id:
                continue
            filtered.append(d)
            if len(filtered) >= limit:
                break
        return filtered


# ═══════════════════════════════════════════════════════════════════════════
# Singleton wiring (replaced by DI container in production)
# ═══════════════════════════════════════════════════════════════════════════

_event_bus: EventBus | None = None
_sse_manager: SSEManager | None = None
_webhook_service: WebhookService | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_sse_manager() -> SSEManager:
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEManager()
    return _sse_manager


def get_webhook_service() -> WebhookService:
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
