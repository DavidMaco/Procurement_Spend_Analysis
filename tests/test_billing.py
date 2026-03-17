"""Tests for billing, subscriptions, and usage metering (billing.py)."""

from __future__ import annotations

import pytest

from procurement_spend_analysis.billing import (
    PLANS,
    BillingInterval,
    BillingService,
    SubscriptionStatus,
    UsageMeter,
    UsageMetric,
)


class TestUsageMeter:
    def test_record_and_get(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=5)
        assert meter.get_usage("t1", UsageMetric.API_CALLS) == 5

    def test_cumulative_recording(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=3)
        meter.record("t1", UsageMetric.API_CALLS, value=7)
        assert meter.get_usage("t1", UsageMetric.API_CALLS) == 10

    def test_separate_tenants(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=5)
        meter.record("t2", UsageMetric.API_CALLS, value=10)
        assert meter.get_usage("t1", UsageMetric.API_CALLS) == 5
        assert meter.get_usage("t2", UsageMetric.API_CALLS) == 10

    def test_get_all_usage(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=5)
        meter.record("t1", UsageMetric.ML_JOBS, value=2)
        all_usage = meter.get_all_usage("t1")
        assert all_usage["api_calls"] == 5
        assert all_usage["ml_jobs"] == 2

    def test_reset_period(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=100)
        meter.reset_period("t1")
        assert meter.get_usage("t1", UsageMetric.API_CALLS) == 0

    def test_check_limit(self):
        meter = UsageMeter()
        meter.record("t1", UsageMetric.API_CALLS, value=80)
        assert meter.check_limit("t1", UsageMetric.API_CALLS, limit=100) is True
        meter.record("t1", UsageMetric.API_CALLS, value=25)
        assert meter.check_limit("t1", UsageMetric.API_CALLS, limit=100) is False


class TestBillingService:
    def test_subscribe_default_plan(self):
        svc = BillingService()
        sub = svc.subscribe("t1")
        assert sub.plan_id == "plan_free"
        assert sub.status == SubscriptionStatus.ACTIVE

    def test_subscribe_starter(self):
        svc = BillingService()
        sub = svc.subscribe("t1", plan_id="plan_starter")
        assert sub.plan_id == "plan_starter"

    def test_get_subscription(self):
        svc = BillingService()
        svc.subscribe("t1")
        sub = svc.get_subscription("t1")
        assert sub is not None
        assert sub.tenant_id == "t1"

    def test_get_nonexistent_subscription(self):
        svc = BillingService()
        assert svc.get_subscription("nonexistent") is None

    def test_upgrade_subscription(self):
        svc = BillingService()
        svc.subscribe("t1", plan_id="plan_free")
        upgraded = svc.upgrade("t1", "plan_professional")
        assert upgraded.plan_id == "plan_professional"

    def test_cancel_subscription(self):
        svc = BillingService()
        svc.subscribe("t1")
        canceled = svc.cancel("t1")
        assert canceled is not None
        assert canceled.status == SubscriptionStatus.CANCELED

    def test_generate_invoice(self):
        svc = BillingService()
        svc.subscribe("t1", plan_id="plan_starter")
        invoice = svc.generate_invoice("t1", "2024-01-01", "2024-01-31")
        assert invoice.total_cents > 0
        assert invoice.tenant_id == "t1"

    def test_list_invoices(self):
        svc = BillingService()
        svc.subscribe("t1", plan_id="plan_starter")
        svc.generate_invoice("t1", "2024-01-01", "2024-01-31")
        svc.generate_invoice("t1", "2024-02-01", "2024-02-29")
        invoices = svc.list_invoices("t1")
        assert len(invoices) == 2

    def test_usage_meter_accessible(self):
        svc = BillingService()
        assert svc.meter is not None
        svc.meter.record("t1", UsageMetric.API_CALLS, value=1)
        assert svc.meter.get_usage("t1", UsageMetric.API_CALLS) == 1


class TestPlans:
    def test_plans_exist(self):
        assert "free" in PLANS
        assert "starter" in PLANS
        assert "professional" in PLANS
        assert "enterprise" in PLANS

    def test_free_plan_is_free(self):
        assert PLANS["free"].price_cents_monthly == 0

    def test_starter_price(self):
        assert PLANS["starter"].price_cents_monthly == 9900  # $99

    def test_professional_price(self):
        assert PLANS["professional"].price_cents_monthly == 49900  # $499
