"""FastAPI router exposing SaaS platform endpoints (v1).

Provides: tenant management, authentication, intelligence engines,
real-time streaming, billing/subscriptions, and webhooks — all behind
JWT + tenant-isolation middleware.
"""

from __future__ import annotations

import dataclasses
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from procurement_spend_analysis.auth import (
    APIKeyService,
    JWTClaims,
    JWTService,
    RateLimiter,
)
from procurement_spend_analysis.billing import PLANS, BillingService, UsageMetric
from procurement_spend_analysis.intelligence import (
    DemandForecastEngine,
    InsightGenerator,
    SavingsOpportunityFinder,
    SpendAnomalyDetector,
    SupplierRiskEngine,
)
from procurement_spend_analysis.streaming import (
    EventType,
    StreamEvent,
    get_event_bus,
    get_sse_manager,
    get_webhook_service,
)
from procurement_spend_analysis.tenant import Tenant, TenantRegistry, TenantTier

# ═══════════════════════════════════════════════════════════════════════════
# Singletons (instantiated once, injected via Depends)
# ═══════════════════════════════════════════════════════════════════════════

_jwt_service: JWTService | None = None
_tenant_registry = TenantRegistry()
_api_key_service = APIKeyService()
_rate_limiter = RateLimiter()
_billing_service = BillingService()
_anomaly_detector = SpendAnomalyDetector()
_forecast_engine = DemandForecastEngine()
_risk_engine = SupplierRiskEngine()
_insight_generator = InsightGenerator()
_savings_finder = SavingsOpportunityFinder()


def _get_jwt_service() -> JWTService:
    global _jwt_service  # noqa: PLW0603
    if _jwt_service is None:
        import os

        secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
        _jwt_service = JWTService(secret=secret)
    return _jwt_service


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI Dependencies
# ═══════════════════════════════════════════════════════════════════════════


async def _extract_claims(request: Request) -> JWTClaims:
    """Extract and validate JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    token = auth_header[7:]
    jwt_svc = _get_jwt_service()
    try:
        return jwt_svc.decode(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def _require_tenant(
    claims: Annotated[JWTClaims, Depends(_extract_claims)],
) -> Tenant:
    """Resolve tenant from JWT claims and enforce active status."""
    try:
        tenant = _tenant_registry.get(claims.tenant_id)
    except KeyError:
        raise HTTPException(status_code=403, detail="Unknown tenant")
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is deactivated")
    return tenant


async def _enforce_rate_limit(
    claims: Annotated[JWTClaims, Depends(_extract_claims)],
    tenant: Annotated[Tenant, Depends(_require_tenant)],
) -> JWTClaims:
    """Token-bucket rate limiting per tenant."""
    allowed = _rate_limiter.consume(
        tenant.tenant_id, tenant.limits.max_api_calls_per_month
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Monthly API rate limit exceeded")
    _billing_service.meter.record(tenant.tenant_id, UsageMetric.API_CALLS)
    return claims


# Type alias for convenience
AuthClaims = Annotated[JWTClaims, Depends(_enforce_rate_limit)]

# ═══════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/v1", tags=["saas-v1"])


# ───────────────────────── Tenants ─────────────────────────


class TenantCreateRequest(BaseModel):
    name: str
    slug: str
    owner_email: str
    tier: TenantTier = TenantTier.FREE
    region: str = "us-east-1"


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    tier: str
    region: str
    is_active: bool
    created_at: str


@router.post("/tenants", response_model=TenantResponse, status_code=201)
def create_tenant(body: TenantCreateRequest) -> TenantResponse:
    tenant = Tenant(
        name=body.name,
        slug=body.slug,
        owner_email=body.owner_email,
        tier=body.tier,
        region=body.region,
    )
    tenant = _tenant_registry.register(tenant)
    _billing_service.subscribe(tenant.tenant_id, f"plan_{tenant.tier.value}")
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        tier=tenant.tier.value,
        region=tenant.region,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, _claims: AuthClaims) -> TenantResponse:
    try:
        t = _tenant_registry.get(tenant_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(
        tenant_id=t.tenant_id,
        name=t.name,
        slug=t.slug,
        tier=t.tier.value,
        region=t.region,
        is_active=t.is_active,
        created_at=t.created_at,
    )


# ───────────────────────── Auth ─────────────────────────


class TokenRequest(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    email: str | None = None
    name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


@router.post("/auth/token", response_model=TokenResponse)
def issue_token(body: TokenRequest) -> TokenResponse:
    """Issue JWT access + refresh tokens for a user."""
    try:
        _tenant_registry.get(body.tenant_id)
    except KeyError:
        raise HTTPException(status_code=400, detail="Unknown tenant_id")
    jwt_svc = _get_jwt_service()
    access = jwt_svc.create_access_token(
        user_id=body.user_id,
        tenant_id=body.tenant_id,
        roles=body.roles,
        email=body.email,
        name=body.name,
    )
    refresh = jwt_svc.create_refresh_token(
        user_id=body.user_id, tenant_id=body.tenant_id
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=list)


class APIKeyResponse(BaseModel):
    key_id: str
    raw_key: str | None = None
    name: str
    prefix: str
    scopes: list[str]
    created_at: str


@router.post("/auth/api-keys", response_model=APIKeyResponse, status_code=201)
def create_api_key(
    body: APIKeyCreateRequest,
    claims: AuthClaims,
) -> APIKeyResponse:
    raw, record = _api_key_service.create(
        tenant_id=claims.tenant_id,
        name=body.name,
        scopes=body.scopes,
    )
    return APIKeyResponse(
        key_id=record.key_id,
        raw_key=raw,
        name=record.name,
        prefix=record.prefix,
        scopes=record.scopes,
        created_at=record.created_at,
    )


@router.get("/auth/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(claims: AuthClaims) -> list[APIKeyResponse]:
    keys = _api_key_service.list_for_tenant(claims.tenant_id)
    return [
        APIKeyResponse(
            key_id=k.key_id,
            name=k.name,
            prefix=k.prefix,
            scopes=k.scopes,
            created_at=k.created_at,
        )
        for k in keys
    ]


# ───────────────────────── Intelligence ─────────────────────────


class IntelligenceSummaryResponse(BaseModel):
    anomalies: list[dict[str, Any]]
    forecasts: list[dict[str, Any]]
    risk_scores: list[dict[str, Any]]
    savings_opportunities: list[dict[str, Any]]
    insights: list[dict[str, Any]]


@router.get("/intelligence/summary", response_model=IntelligenceSummaryResponse)
def intelligence_summary(claims: AuthClaims) -> IntelligenceSummaryResponse:
    """Return a combined intelligence summary using demo data.

    In production this would pull from the tenant's data lake; for now
    we generate a representative demo bundle.
    """
    from dashboard_data import generate_demo_bundle

    bundle = generate_demo_bundle(num_orders=2500, seed=42, num_quality_incidents=150)
    po_df = bundle["raw"]["purchase_orders"]
    supp_df = bundle["raw"]["suppliers"]
    qi_df = bundle["raw"]["quality_incidents"]

    anomalies = _anomaly_detector.detect(po_df)
    risks = _risk_engine.assess(supp_df, po_df, qi_df)
    savings = _savings_finder.find(po_df, supp_df)

    forecasts = _forecast_engine.forecast(
        po_df, date_col="po_date", value_col="quantity"
    )
    context = {
        "insights": bundle["insights"],
        "analytics": bundle["analytics"],
        "forecasts": forecasts,
    }
    nl_insights = _insight_generator.generate(context)

    _billing_service.meter.record(claims.tenant_id, UsageMetric.ML_JOBS)
    get_event_bus().publish(
        StreamEvent(
            event_type=EventType.JOB_COMPLETED.value,
            tenant_id=claims.tenant_id,
            payload={"job": "intelligence_summary"},
            source="intelligence",
        )
    )

    return IntelligenceSummaryResponse(
        anomalies=[dataclasses.asdict(a) for a in anomalies[:20]],
        forecasts=[dataclasses.asdict(f) for f in forecasts[:20]],
        risk_scores=[dataclasses.asdict(r) for r in risks[:20]],
        savings_opportunities=[dataclasses.asdict(s) for s in savings[:20]],
        insights=[dataclasses.asdict(i) for i in nl_insights],
    )


@router.get("/intelligence/forecast")
def demand_forecast(claims: AuthClaims) -> dict[str, Any]:
    from dashboard_data import generate_demo_bundle

    bundle = generate_demo_bundle(2500, 42, 150)
    forecasts = _forecast_engine.forecast(
        bundle["raw"]["purchase_orders"],
        date_col="po_date",
        value_col="quantity",
    )
    _billing_service.meter.record(claims.tenant_id, UsageMetric.ML_JOBS)
    return {
        "forecasts": [dataclasses.asdict(f) for f in forecasts],
        "count": len(forecasts),
    }


@router.get("/intelligence/anomalies")
def detect_anomalies(claims: AuthClaims) -> dict[str, Any]:
    from dashboard_data import generate_demo_bundle

    bundle = generate_demo_bundle(2500, 42, 150)
    anomalies = _anomaly_detector.detect(bundle["raw"]["purchase_orders"])
    _billing_service.meter.record(claims.tenant_id, UsageMetric.ML_JOBS)
    return {
        "anomalies": [dataclasses.asdict(a) for a in anomalies],
        "count": len(anomalies),
    }


@router.get("/intelligence/risk-scores")
def supplier_risk_scores(claims: AuthClaims) -> dict[str, Any]:
    from dashboard_data import generate_demo_bundle

    bundle = generate_demo_bundle(2500, 42, 150)
    scores = _risk_engine.assess(
        bundle["raw"]["suppliers"],
        bundle["raw"]["purchase_orders"],
        bundle["raw"]["quality_incidents"],
    )
    _billing_service.meter.record(claims.tenant_id, UsageMetric.ML_JOBS)
    return {
        "risk_scores": [dataclasses.asdict(s) for s in scores],
        "count": len(scores),
    }


@router.get("/intelligence/savings")
def savings_opportunities(claims: AuthClaims) -> dict[str, Any]:
    from dashboard_data import generate_demo_bundle

    bundle = generate_demo_bundle(2500, 42, 150)
    opps = _savings_finder.find(
        bundle["raw"]["purchase_orders"], bundle["raw"]["suppliers"]
    )
    _billing_service.meter.record(claims.tenant_id, UsageMetric.ML_JOBS)
    return {"opportunities": [dataclasses.asdict(o) for o in opps], "count": len(opps)}


# ───────────────────────── Streaming / SSE ─────────────────────────


@router.get("/events/stream")
async def event_stream(claims: AuthClaims) -> StreamingResponse:
    """Server-Sent Events stream for real-time tenant notifications."""
    tenant = _tenant_registry.get(claims.tenant_id)
    if not tenant.limits.realtime_streaming:
        raise HTTPException(
            status_code=403,
            detail="Real-time streaming requires Professional tier or above",
        )
    sse_manager = get_sse_manager()
    return StreamingResponse(
        sse_manager.stream(claims.tenant_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/events/recent")
def recent_events(
    claims: AuthClaims,
    limit: int = Query(default=50, le=200),
    event_type: str | None = None,
) -> dict[str, Any]:
    events = get_event_bus().recent_events(
        limit=limit,
        event_type=event_type,
        tenant_id=claims.tenant_id,
    )
    return {"events": [dataclasses.asdict(e) for e in events], "count": len(events)}


# ───────────────────────── Webhooks ─────────────────────────


class WebhookCreateRequest(BaseModel):
    url: str
    event_types: list[str] = Field(default_factory=list)
    description: str = ""


class WebhookResponse(BaseModel):
    webhook_id: str
    url: str
    event_types: list[str]
    status: str
    created_at: str
    description: str


@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
def register_webhook(body: WebhookCreateRequest, claims: AuthClaims) -> WebhookResponse:
    tenant = _tenant_registry.get(claims.tenant_id)
    existing = get_webhook_service().list_for_tenant(claims.tenant_id)
    if len(existing) >= tenant.limits.max_webhooks:
        raise HTTPException(
            status_code=403, detail="Webhook limit reached for your tier"
        )
    ep = get_webhook_service().register(
        tenant_id=claims.tenant_id,
        url=body.url,
        event_types=body.event_types,
        description=body.description,
    )
    return WebhookResponse(
        webhook_id=ep.webhook_id,
        url=ep.url,
        event_types=ep.event_types,
        status=ep.status.value,
        created_at=ep.created_at,
        description=ep.description,
    )


@router.get("/webhooks", response_model=list[WebhookResponse])
def list_webhooks(claims: AuthClaims) -> list[WebhookResponse]:
    endpoints = get_webhook_service().list_for_tenant(claims.tenant_id)
    return [
        WebhookResponse(
            webhook_id=ep.webhook_id,
            url=ep.url,
            event_types=ep.event_types,
            status=ep.status.value,
            created_at=ep.created_at,
            description=ep.description,
        )
        for ep in endpoints
    ]


@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: str, claims: AuthClaims) -> None:
    get_webhook_service().delete(webhook_id)


# ───────────────────────── Billing ─────────────────────────


class SubscriptionResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    plan_id: str
    status: str
    billing_interval: str
    current_period_start: str
    current_period_end: str


class UpgradeRequest(BaseModel):
    plan_id: str


@router.get("/billing/plans")
def list_plans() -> dict[str, Any]:
    """Public endpoint — no auth required."""
    return {
        "plans": [
            {
                "plan_id": p.plan_id,
                "name": p.name,
                "tier": p.tier,
                "price_monthly_cents": p.price_cents_monthly,
                "price_annual_cents": p.price_cents_annual,
                "features": p.features,
            }
            for p in PLANS.values()
            if p.is_public
        ]
    }


@router.get("/billing/subscription", response_model=SubscriptionResponse)
def get_subscription(claims: AuthClaims) -> SubscriptionResponse:
    sub = _billing_service.get_subscription(claims.tenant_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="No active subscription")
    return SubscriptionResponse(
        subscription_id=sub.subscription_id,
        tenant_id=sub.tenant_id,
        plan_id=sub.plan_id,
        status=sub.status.value,
        billing_interval=sub.billing_interval.value,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
    )


@router.post("/billing/upgrade", response_model=SubscriptionResponse)
def upgrade_subscription(
    body: UpgradeRequest, claims: AuthClaims
) -> SubscriptionResponse:
    try:
        sub = _billing_service.upgrade(claims.tenant_id, body.plan_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubscriptionResponse(
        subscription_id=sub.subscription_id,
        tenant_id=sub.tenant_id,
        plan_id=sub.plan_id,
        status=sub.status.value,
        billing_interval=sub.billing_interval.value,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
    )


@router.get("/billing/usage")
def get_usage(claims: AuthClaims) -> dict[str, Any]:
    usage = _billing_service.meter.get_all_usage(claims.tenant_id)
    remaining = _rate_limiter.remaining(
        claims.tenant_id,
        _tenant_registry.get(claims.tenant_id).limits.max_api_calls_per_month,
    )
    return {"usage": usage, "api_calls_remaining": remaining}


@router.get("/billing/invoices")
def list_invoices(claims: AuthClaims) -> dict[str, Any]:
    invoices = _billing_service.list_invoices(claims.tenant_id)
    return {
        "invoices": [
            {
                "invoice_id": inv.invoice_id,
                "period": f"{inv.period_start} — {inv.period_end}",
                "total_cents": inv.total_cents,
                "currency": inv.currency,
                "status": inv.status,
            }
            for inv in invoices
        ]
    }
