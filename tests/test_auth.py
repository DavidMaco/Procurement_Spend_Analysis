"""Tests for JWT auth, API key management, and rate limiting (auth.py)."""

from __future__ import annotations

import time

import pytest

from procurement_spend_analysis.auth import (
    APIKeyService,
    JWTClaims,
    JWTService,
    RateLimiter,
)


class TestJWTService:
    def setup_method(self):
        self.svc = JWTService(secret="test-secret-key-minimum-32-chars!")

    def test_encode_decode_roundtrip(self):
        claims = JWTClaims(sub="user1", tenant_id="tenant1", roles=["admin"])
        token = self.svc.encode(claims)
        decoded = self.svc.decode(token)
        assert decoded.sub == "user1"
        assert decoded.tenant_id == "tenant1"
        assert "admin" in decoded.roles

    def test_create_access_token(self):
        token = self.svc.create_access_token(
            user_id="u1",
            tenant_id="t1",
            roles=["analyst"],
            email="u1@test.com",
        )
        claims = self.svc.decode(token)
        assert claims.sub == "u1"
        assert claims.tenant_id == "t1"
        assert claims.email == "u1@test.com"

    def test_create_refresh_token(self):
        token = self.svc.create_refresh_token(user_id="u1", tenant_id="t1")
        claims = self.svc.decode(token)
        assert claims.sub == "u1"
        # Refresh tokens have longer expiry
        assert claims.exp > time.time() + 86400

    def test_expired_token_raises(self):
        claims = JWTClaims(sub="u1", tenant_id="t1", exp=int(time.time()) - 10)
        token = self.svc.encode(claims)
        with pytest.raises(ValueError, match="expired"):
            self.svc.decode(token)

    def test_tampered_token_raises(self):
        token = self.svc.create_access_token(user_id="u1", tenant_id="t1")
        # Tamper with the payload
        parts = token.split(".")
        parts[1] = parts[1][:-2] + "XX"
        tampered = ".".join(parts)
        with pytest.raises(ValueError):
            self.svc.decode(tampered)

    def test_wrong_secret_raises(self):
        token = self.svc.create_access_token(user_id="u1", tenant_id="t1")
        other_svc = JWTService(secret="different-secret-key-minimum-32!!")
        with pytest.raises(ValueError):
            other_svc.decode(token)


class TestAPIKeyService:
    def setup_method(self):
        self.svc = APIKeyService()

    def test_create_and_validate(self):
        raw_key, record = self.svc.create(tenant_id="t1", name="test-key")
        assert raw_key.startswith("pi_live_")
        assert record.tenant_id == "t1"
        validated = self.svc.validate(raw_key)
        assert validated.key_id == record.key_id

    def test_validate_invalid_key_raises(self):
        with pytest.raises(ValueError, match="Invalid"):
            self.svc.validate("pi_sk_bogus_key_that_does_not_exist")

    def test_revoke_key(self):
        raw_key, record = self.svc.create(tenant_id="t1", name="revokable")
        revoked = self.svc.revoke(record.key_id)
        assert revoked.is_active is False
        with pytest.raises(ValueError):
            self.svc.validate(raw_key)

    def test_list_for_tenant(self):
        self.svc.create(tenant_id="t1", name="key1")
        self.svc.create(tenant_id="t1", name="key2")
        self.svc.create(tenant_id="t2", name="key3")
        t1_keys = self.svc.list_for_tenant("t1")
        assert len(t1_keys) == 2

    def test_create_with_scopes(self):
        _, record = self.svc.create(tenant_id="t1", name="scoped", scopes=["read", "write"])
        assert record.scopes == ["read", "write"]


class TestRateLimiter:
    def test_consume_within_limit(self):
        rl = RateLimiter()
        assert rl.consume("t1", max_per_month=100) is True

    def test_consume_exceeds_limit(self):
        rl = RateLimiter()
        for _ in range(10):
            rl.consume("t1", max_per_month=10)
        assert rl.consume("t1", max_per_month=10) is False

    def test_remaining(self):
        rl = RateLimiter()
        rl.consume("t1", max_per_month=100, cost=30)
        assert rl.remaining("t1", max_per_month=100) == 70

    def test_separate_tenants(self):
        rl = RateLimiter()
        for _ in range(10):
            rl.consume("t1", max_per_month=10)
        # t2 should still have capacity
        assert rl.consume("t2", max_per_month=10) is True
