"""Multi-tenant isolation layer for the Procurement Intelligence SaaS.

Every request is scoped to a tenant (organisation). Tenant context propagates
through the call stack via a context-var so that lower layers (event log,
metrics, ML jobs) can read the active tenant without explicit threading.

Supports three deployment modes:
  - **shared**: all tenants share compute, data partitioned by tenant_id.
  - **pooled**: tenants share a DB cluster but get isolated schemas.
  - **dedicated**: enterprise tenants get their own compute + storage.
"""

from __future__ import annotations

import contextvars
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Context-var for request-scoped tenant propagation
# ---------------------------------------------------------------------------

_current_tenant: contextvars.ContextVar[Optional["Tenant"]] = contextvars.ContextVar(
    "current_tenant",
    default=None,
)


def set_current_tenant(tenant: "Tenant") -> contextvars.Token:
    return _current_tenant.set(tenant)


def get_current_tenant() -> Optional["Tenant"]:
    return _current_tenant.get()


def require_current_tenant() -> "Tenant":
    tenant = _current_tenant.get()
    if tenant is None:
        raise RuntimeError("No tenant context — authenticate first")
    return tenant


# ---------------------------------------------------------------------------
# Tenant model
# ---------------------------------------------------------------------------


class TenantTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class IsolationMode(str, Enum):
    SHARED = "shared"
    POOLED = "pooled"
    DEDICATED = "dedicated"


class TenantLimits(BaseModel):
    """Usage limits enforced per billing tier."""

    max_users: int = 5
    max_api_calls_per_month: int = 10_000
    max_upload_rows: int = 100_000
    max_storage_gb: float = 1.0
    max_ml_jobs_per_day: int = 10
    max_webhooks: int = 3
    realtime_streaming: bool = False
    custom_branding: bool = False
    sso_enabled: bool = False
    dedicated_support: bool = False
    data_retention_days: int = 90


TIER_LIMITS: dict[TenantTier, TenantLimits] = {
    TenantTier.FREE: TenantLimits(),
    TenantTier.STARTER: TenantLimits(
        max_users=25,
        max_api_calls_per_month=100_000,
        max_upload_rows=1_000_000,
        max_storage_gb=10.0,
        max_ml_jobs_per_day=50,
        max_webhooks=10,
        realtime_streaming=True,
        data_retention_days=365,
    ),
    TenantTier.PROFESSIONAL: TenantLimits(
        max_users=100,
        max_api_calls_per_month=1_000_000,
        max_upload_rows=10_000_000,
        max_storage_gb=100.0,
        max_ml_jobs_per_day=500,
        max_webhooks=50,
        realtime_streaming=True,
        custom_branding=True,
        sso_enabled=True,
        data_retention_days=730,
    ),
    TenantTier.ENTERPRISE: TenantLimits(
        max_users=10_000,
        max_api_calls_per_month=100_000_000,
        max_upload_rows=100_000_000,
        max_storage_gb=10_000.0,
        max_ml_jobs_per_day=10_000,
        max_webhooks=500,
        realtime_streaming=True,
        custom_branding=True,
        sso_enabled=True,
        dedicated_support=True,
        data_retention_days=3650,
    ),
}


class Tenant(BaseModel):
    """Organisation record — the fundamental isolation boundary."""

    tenant_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    slug: str  # URL-safe identifier, e.g. "acme-corp"
    tier: TenantTier = TenantTier.FREE
    isolation_mode: IsolationMode = IsolationMode.SHARED
    owner_email: str
    region: str = "us-east-1"  # AWS region for data residency
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    @property
    def limits(self) -> TenantLimits:
        return TIER_LIMITS[self.tier]

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# In-memory tenant registry (replaced by DynamoDB/Postgres in production)
# ---------------------------------------------------------------------------


class TenantRegistry:
    """Thread-safe tenant store with CRUD operations."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._by_slug: dict[str, str] = {}

    def register(self, tenant: Tenant) -> Tenant:
        if tenant.slug in self._by_slug:
            raise ValueError(f"Tenant slug '{tenant.slug}' already registered")
        self._tenants[tenant.tenant_id] = tenant
        self._by_slug[tenant.slug] = tenant.tenant_id
        return tenant

    def get(self, tenant_id: str) -> Tenant:
        if tenant_id not in self._tenants:
            raise KeyError(f"Tenant '{tenant_id}' not found")
        return self._tenants[tenant_id]

    def get_by_slug(self, slug: str) -> Tenant:
        tid = self._by_slug.get(slug)
        if tid is None:
            raise KeyError(f"Tenant slug '{slug}' not found")
        return self._tenants[tid]

    def list_all(self) -> list[Tenant]:
        return list(self._tenants.values())

    def deactivate(self, tenant_id: str) -> Tenant:
        old = self.get(tenant_id)
        updated = Tenant(
            tenant_id=old.tenant_id,
            name=old.name,
            slug=old.slug,
            tier=old.tier,
            isolation_mode=old.isolation_mode,
            owner_email=old.owner_email,
            region=old.region,
            created_at=old.created_at,
            metadata=old.metadata,
            is_active=False,
        )
        self._tenants[old.tenant_id] = updated
        return updated

    def upgrade_tier(self, tenant_id: str, new_tier: TenantTier) -> Tenant:
        old = self.get(tenant_id)
        updated = Tenant(
            tenant_id=old.tenant_id,
            name=old.name,
            slug=old.slug,
            tier=new_tier,
            isolation_mode=old.isolation_mode,
            owner_email=old.owner_email,
            region=old.region,
            created_at=old.created_at,
            metadata=old.metadata,
            is_active=old.is_active,
        )
        self._tenants[old.tenant_id] = updated
        return updated

    def count(self) -> int:
        return len(self._tenants)
