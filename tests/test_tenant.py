"""Tests for multi-tenant SaaS foundation (tenant.py)."""

from __future__ import annotations

import pytest

from procurement_spend_analysis.tenant import (
    TIER_LIMITS,
    Tenant,
    TenantRegistry,
    TenantTier,
    get_current_tenant,
    require_current_tenant,
    set_current_tenant,
)


class TestTenantModel:
    def test_create_tenant_defaults(self):
        t = Tenant(name="Acme Corp", slug="acme", owner_email="admin@acme.com")
        assert t.tier == TenantTier.FREE
        assert t.is_active is True
        assert t.region == "us-east-1"
        assert len(t.tenant_id) == 32

    def test_tenant_limits_from_tier(self):
        t = Tenant(name="Pro Corp", slug="pro", owner_email="a@b.com", tier=TenantTier.PROFESSIONAL)
        limits = t.limits
        assert limits.max_users == TIER_LIMITS[TenantTier.PROFESSIONAL].max_users
        assert limits.sso_enabled is True

    def test_free_tier_limits(self):
        limits = TIER_LIMITS[TenantTier.FREE]
        assert limits.max_users == 5
        assert limits.max_webhooks == 3
        assert limits.realtime_streaming is False

    def test_enterprise_tier_limits(self):
        limits = TIER_LIMITS[TenantTier.ENTERPRISE]
        assert limits.max_users == 10_000
        assert limits.dedicated_support is True
        assert limits.realtime_streaming is True


class TestTenantContextVar:
    def test_no_tenant_by_default(self):
        assert get_current_tenant() is None

    def test_set_and_get_tenant(self):
        t = Tenant(name="Test", slug="test", owner_email="t@t.com")
        token = set_current_tenant(t)
        assert get_current_tenant() == t
        # Reset context var for other tests
        from procurement_spend_analysis.tenant import _current_tenant
        _current_tenant.reset(token)

    def test_require_raises_when_missing(self):
        # Ensure no tenant set
        assert get_current_tenant() is None
        with pytest.raises(RuntimeError, match="No tenant context"):
            require_current_tenant()


class TestTenantRegistry:
    def test_register_and_get(self):
        reg = TenantRegistry()
        t = Tenant(name="Corp", slug="corp", owner_email="a@b.com")
        reg.register(t)
        assert reg.get(t.tenant_id) == t

    def test_get_by_slug(self):
        reg = TenantRegistry()
        t = Tenant(name="Slug Corp", slug="slug-corp", owner_email="a@b.com")
        reg.register(t)
        assert reg.get_by_slug("slug-corp") == t

    def test_get_nonexistent_raises(self):
        reg = TenantRegistry()
        with pytest.raises(KeyError):
            reg.get("nonexistent")

    def test_deactivate(self):
        reg = TenantRegistry()
        t = Tenant(name="D", slug="d", owner_email="a@b.com")
        reg.register(t)
        updated = reg.deactivate(t.tenant_id)
        assert updated.is_active is False

    def test_upgrade_tier(self):
        reg = TenantRegistry()
        t = Tenant(name="U", slug="u", owner_email="a@b.com", tier=TenantTier.FREE)
        reg.register(t)
        upgraded = reg.upgrade_tier(t.tenant_id, TenantTier.PROFESSIONAL)
        assert upgraded.tier == TenantTier.PROFESSIONAL

    def test_list_all(self):
        reg = TenantRegistry()
        for i in range(3):
            reg.register(Tenant(name=f"T{i}", slug=f"t{i}", owner_email=f"t{i}@t.com"))
        assert reg.count() == 3
        assert len(reg.list_all()) == 3

    def test_duplicate_slug_raises(self):
        reg = TenantRegistry()
        t1 = Tenant(name="A", slug="same", owner_email="a@a.com")
        reg.register(t1)
        t2 = Tenant(name="B", slug="same", owner_email="b@b.com")
        with pytest.raises(ValueError, match="slug"):
            reg.register(t2)
