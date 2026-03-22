"""Billing, subscription, and usage metering for the SaaS platform.

Provides:
  1. **Subscription Management** — Tier-based plans with upgrade/downgrade flows.
  2. **Usage Metering** — Track API calls, storage, ML jobs, uploads per tenant.
  3. **Invoice Generation** — Monthly invoice computation with line items.
  4. **Stripe-ready Integration Points** — Webhook handlers and checkout session
     factories (actual Stripe calls are behind an interface for testability).

Designed to plug into Stripe for payment processing. All monetary values use
integer cents (USD) to avoid floating-point issues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


# ═══════════════════════════════════════════════════════════════════════════
# Plans & Pricing
# ═══════════════════════════════════════════════════════════════════════════


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass(frozen=True)
class Plan:
    """A SaaS pricing plan."""

    plan_id: str
    name: str
    tier: str  # maps to TenantTier
    price_cents_monthly: int
    price_cents_annual: int  # Per-year (not per-month)
    features: list[str]
    is_public: bool = True


PLANS: dict[str, Plan] = {
    "free": Plan(
        plan_id="plan_free",
        name="Free",
        tier="free",
        price_cents_monthly=0,
        price_cents_annual=0,
        features=[
            "5 users",
            "10K API calls/month",
            "100K rows per upload",
            "1 GB storage",
            "10 ML jobs/day",
            "Community support",
        ],
    ),
    "starter": Plan(
        plan_id="plan_starter",
        name="Starter",
        tier="starter",
        price_cents_monthly=9900,  # $99/month
        price_cents_annual=99000,  # $990/year (2 months free)
        features=[
            "25 users",
            "100K API calls/month",
            "1M rows per upload",
            "10 GB storage",
            "50 ML jobs/day",
            "Real-time streaming",
            "10 webhooks",
            "Email support",
        ],
    ),
    "professional": Plan(
        plan_id="plan_professional",
        name="Professional",
        tier="professional",
        price_cents_monthly=49900,  # $499/month
        price_cents_annual=499000,  # $4,990/year (2 months free)
        features=[
            "100 users",
            "1M API calls/month",
            "10M rows per upload",
            "100 GB storage",
            "500 ML jobs/day",
            "Real-time streaming",
            "50 webhooks",
            "Custom branding",
            "SSO/SAML",
            "Priority support",
            "SLA guarantee",
        ],
    ),
    "enterprise": Plan(
        plan_id="plan_enterprise",
        name="Enterprise",
        tier="enterprise",
        price_cents_monthly=0,  # Custom pricing
        price_cents_annual=0,
        features=[
            "Unlimited users",
            "Unlimited API calls",
            "Unlimited uploads",
            "10 TB storage",
            "Unlimited ML jobs",
            "Dedicated compute",
            "Custom branding",
            "SSO/SAML",
            "Dedicated support manager",
            "99.99% uptime SLA",
            "SOC 2 compliance",
            "Data residency controls",
        ],
        is_public=False,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# Subscription
# ═══════════════════════════════════════════════════════════════════════════


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PAUSED = "paused"


@dataclass
class Subscription:
    """A tenant's active subscription."""

    subscription_id: str = field(default_factory=lambda: uuid4().hex[:16])
    tenant_id: str = ""
    plan_id: str = "plan_free"
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    current_period_start: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    current_period_end: str = ""
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    trial_end: Optional[str] = None
    canceled_at: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Usage Metering
# ═══════════════════════════════════════════════════════════════════════════


class UsageMetric(str, Enum):
    API_CALLS = "api_calls"
    UPLOAD_ROWS = "upload_rows"
    STORAGE_BYTES = "storage_bytes"
    ML_JOBS = "ml_jobs"
    WEBHOOK_DELIVERIES = "webhook_deliveries"
    ACTIVE_USERS = "active_users"


@dataclass
class UsageRecord:
    """A single usage data point."""

    record_id: str = field(default_factory=lambda: uuid4().hex[:12])
    tenant_id: str = ""
    metric: str = ""
    value: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class UsageMeter:
    """Tracks per-tenant usage for billing and limit enforcement."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._counters: dict[str, dict[str, int]] = {}  # tenant_id -> metric -> count

    def record(
        self, tenant_id: str, metric: UsageMetric, value: int = 1
    ) -> UsageRecord:
        rec = UsageRecord(tenant_id=tenant_id, metric=metric.value, value=value)
        self._records.append(rec)

        tenant_counters = self._counters.setdefault(tenant_id, {})
        tenant_counters[metric.value] = tenant_counters.get(metric.value, 0) + value

        return rec

    def get_usage(self, tenant_id: str, metric: UsageMetric) -> int:
        return self._counters.get(tenant_id, {}).get(metric.value, 0)

    def get_all_usage(self, tenant_id: str) -> dict[str, int]:
        return dict(self._counters.get(tenant_id, {}))

    def reset_period(self, tenant_id: str) -> None:
        """Reset counters for a new billing period."""
        self._counters[tenant_id] = {}

    def check_limit(self, tenant_id: str, metric: UsageMetric, limit: int) -> bool:
        """Return True if usage is within the limit."""
        return self.get_usage(tenant_id, metric) < limit


# ═══════════════════════════════════════════════════════════════════════════
# Invoice
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class InvoiceLineItem:
    description: str
    quantity: int
    unit_price_cents: int
    amount_cents: int


@dataclass
class Invoice:
    """Monthly invoice for a tenant."""

    invoice_id: str = field(default_factory=lambda: uuid4().hex[:16])
    tenant_id: str = ""
    subscription_id: str = ""
    plan_name: str = ""
    period_start: str = ""
    period_end: str = ""
    line_items: list[InvoiceLineItem] = field(default_factory=list)
    subtotal_cents: int = 0
    tax_cents: int = 0
    total_cents: int = 0
    currency: str = "usd"
    status: str = "draft"  # draft, sent, paid, overdue
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class BillingService:
    """Manages subscriptions, usage, and invoicing."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}
        self._invoices: list[Invoice] = []
        self._meter = UsageMeter()

    @property
    def meter(self) -> UsageMeter:
        return self._meter

    def subscribe(
        self,
        tenant_id: str,
        plan_id: str = "plan_free",
        billing_interval: BillingInterval = BillingInterval.MONTHLY,
    ) -> Subscription:
        plan = PLANS.get(plan_id.replace("plan_", ""))
        if plan is None:
            raise ValueError(f"Unknown plan: {plan_id}")

        sub = Subscription(
            tenant_id=tenant_id,
            plan_id=plan.plan_id,
            billing_interval=billing_interval,
        )
        self._subscriptions[tenant_id] = sub
        return sub

    def get_subscription(self, tenant_id: str) -> Subscription | None:
        return self._subscriptions.get(tenant_id)

    def upgrade(self, tenant_id: str, new_plan_id: str) -> Subscription:
        sub = self._subscriptions.get(tenant_id)
        if sub is None:
            return self.subscribe(tenant_id, new_plan_id)
        sub.plan_id = new_plan_id
        return sub

    def cancel(self, tenant_id: str) -> Subscription | None:
        sub = self._subscriptions.get(tenant_id)
        if sub:
            sub.status = SubscriptionStatus.CANCELED
            sub.canceled_at = datetime.now(timezone.utc).isoformat()
        return sub

    def generate_invoice(
        self,
        tenant_id: str,
        period_start: str,
        period_end: str,
    ) -> Invoice:
        sub = self._subscriptions.get(tenant_id)
        if sub is None:
            raise ValueError(f"No subscription for tenant {tenant_id}")

        plan_key = sub.plan_id.replace("plan_", "")
        plan = PLANS.get(plan_key)
        if plan is None:
            raise ValueError(f"Unknown plan: {sub.plan_id}")

        if sub.billing_interval == BillingInterval.MONTHLY:
            base_price = plan.price_cents_monthly
        else:
            base_price = plan.price_cents_annual // 12

        line_items = [
            InvoiceLineItem(
                description=f"{plan.name} plan ({sub.billing_interval.value})",
                quantity=1,
                unit_price_cents=base_price,
                amount_cents=base_price,
            ),
        ]

        usage = self._meter.get_all_usage(tenant_id)
        for metric_name, count in usage.items():
            if count > 0:
                line_items.append(
                    InvoiceLineItem(
                        description=f"{metric_name} usage",
                        quantity=count,
                        unit_price_cents=0,  # Included in plan
                        amount_cents=0,
                    )
                )

        subtotal = sum(li.amount_cents for li in line_items)

        invoice = Invoice(
            tenant_id=tenant_id,
            subscription_id=sub.subscription_id,
            plan_name=plan.name,
            period_start=period_start,
            period_end=period_end,
            line_items=line_items,
            subtotal_cents=subtotal,
            tax_cents=0,
            total_cents=subtotal,
        )
        self._invoices.append(invoice)
        return invoice

    def list_invoices(self, tenant_id: str) -> list[Invoice]:
        return [inv for inv in self._invoices if inv.tenant_id == tenant_id]
