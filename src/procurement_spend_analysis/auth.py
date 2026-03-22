"""JWT + API-key authentication for the Procurement Intelligence SaaS.

Supports three authentication flows:
  1. **JWT Bearer** — for dashboard users and SSO-federated identities.
  2. **API Key** — for programmatic access (SDK, CI/CD, webhooks).
  3. **Service Token** — for internal microservice-to-microservice calls.

All tokens carry a tenant_id claim so that every downstream operation is
automatically scoped to the correct organisation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------


class TokenType(str, Enum):
    JWT = "jwt"
    API_KEY = "api_key"
    SERVICE = "service"


# ---------------------------------------------------------------------------
# JWT implementation (HMAC-SHA256, no external deps)
# ---------------------------------------------------------------------------

_DEFAULT_TTL_SECONDS = 3600  # 1 hour
_REFRESH_TTL_SECONDS = 86400 * 30  # 30 days


def _b64url_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return urlsafe_b64decode(s + "=" * padding)


class JWTClaims(BaseModel):
    """Standard + custom claims embedded in access tokens."""

    sub: str  # user_id
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    email: Optional[str] = None
    name: Optional[str] = None
    iat: int = Field(default_factory=lambda: int(time.time()))
    exp: int = Field(default_factory=lambda: int(time.time()) + _DEFAULT_TTL_SECONDS)
    jti: str = Field(default_factory=lambda: uuid4().hex)
    iss: str = "procurement-intelligence-saas"
    aud: str = "procurement-api"
    token_type: TokenType = TokenType.JWT


class JWTService:
    """Symmetric HMAC-SHA256 JWT encoder/decoder.

    In production, swap this for RS256 with rotating key pairs via AWS KMS
    or an external IdP (Auth0 / Cognito / Clerk).
    """

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def encode(self, claims: JWTClaims) -> str:
        header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64url_encode(claims.model_dump_json().encode())
        signature = self._sign(f"{header}.{payload}")
        return f"{header}.{payload}.{signature}"

    def decode(self, token: str) -> JWTClaims:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT")
        header_b64, payload_b64, sig_b64 = parts

        expected_sig = self._sign(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(sig_b64, expected_sig):
            raise ValueError("Invalid JWT signature")

        payload_bytes = _b64url_decode(payload_b64)
        claims = JWTClaims.model_validate_json(payload_bytes)

        if claims.exp < int(time.time()):
            raise ValueError("JWT expired")

        return claims

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        email: str | None = None,
        name: str | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> str:
        now = int(time.time())
        claims = JWTClaims(
            sub=user_id,
            tenant_id=tenant_id,
            roles=roles or [],
            permissions=permissions or [],
            email=email,
            name=name,
            iat=now,
            exp=now + ttl_seconds,
        )
        return self.encode(claims)

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
    ) -> str:
        now = int(time.time())
        claims = JWTClaims(
            sub=user_id,
            tenant_id=tenant_id,
            iat=now,
            exp=now + _REFRESH_TTL_SECONDS,
        )
        return self.encode(claims)

    def _sign(self, message: str) -> str:
        sig = hmac.new(self._secret, message.encode(), hashlib.sha256).digest()
        return _b64url_encode(sig)


# ---------------------------------------------------------------------------
# API Key management
# ---------------------------------------------------------------------------


class APIKey(BaseModel):
    """Persistent API key record."""

    key_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    tenant_id: str
    name: str
    key_hash: str  # SHA-256 hash of the raw key — never store raw
    prefix: str  # first 8 chars for identification, e.g. "pi_live_"
    scopes: list[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: Optional[str] = None
    is_active: bool = True
    last_used_at: Optional[str] = None
    usage_count: int = 0

    model_config = {"frozen": True}


class APIKeyService:
    """Create, validate, and revoke API keys.

    Keys are stored hashed. The raw key is returned only once at creation.
    """

    _PREFIX = "pi_live_"

    def __init__(self) -> None:
        self._keys: dict[str, APIKey] = {}  # key_id -> APIKey
        self._hash_index: dict[str, str] = {}  # key_hash -> key_id

    @staticmethod
    def _hash_key(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    def create(
        self,
        tenant_id: str,
        name: str,
        scopes: list[str] | None = None,
    ) -> tuple[str, APIKey]:
        """Generate a new API key. Returns (raw_key, APIKey record)."""
        raw = f"{self._PREFIX}{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw)
        record = APIKey(
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            prefix=raw[:16],
            scopes=scopes or [],
        )
        self._keys[record.key_id] = record
        self._hash_index[key_hash] = record.key_id
        return raw, record

    def validate(self, raw_key: str) -> APIKey:
        """Look up a key by its hash. Raises ValueError if invalid or inactive."""
        h = self._hash_key(raw_key)
        key_id = self._hash_index.get(h)
        if key_id is None:
            raise ValueError("Invalid API key")
        record = self._keys[key_id]
        if not record.is_active:
            raise ValueError("API key is revoked")
        if record.expires_at:
            exp = datetime.fromisoformat(record.expires_at)
            if datetime.now(timezone.utc) > exp:
                raise ValueError("API key expired")
        return record

    def revoke(self, key_id: str) -> APIKey:
        if key_id not in self._keys:
            raise KeyError(f"API key '{key_id}' not found")
        old = self._keys[key_id]
        updated = APIKey(
            key_id=old.key_id,
            tenant_id=old.tenant_id,
            name=old.name,
            key_hash=old.key_hash,
            prefix=old.prefix,
            scopes=old.scopes,
            created_at=old.created_at,
            expires_at=old.expires_at,
            is_active=False,
            last_used_at=old.last_used_at,
            usage_count=old.usage_count,
        )
        self._keys[key_id] = updated
        return updated

    def list_for_tenant(self, tenant_id: str) -> list[APIKey]:
        return [k for k in self._keys.values() if k.tenant_id == tenant_id]


# ---------------------------------------------------------------------------
# Rate limiting (token bucket)
# ---------------------------------------------------------------------------


class RateLimiter:
    """Per-tenant token-bucket rate limiter.

    Each tenant gets a bucket sized to their tier's monthly API limit,
    refilled proportionally per second.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, Any]] = {}

    def _ensure_bucket(self, tenant_id: str, max_per_month: int) -> dict[str, Any]:
        if tenant_id not in self._buckets:
            tokens_per_second = max_per_month / (30 * 24 * 3600)
            self._buckets[tenant_id] = {
                "tokens": float(max_per_month),
                "max_tokens": float(max_per_month),
                "refill_rate": tokens_per_second,
                "last_refill": time.monotonic(),
            }
        return self._buckets[tenant_id]

    def consume(self, tenant_id: str, max_per_month: int, cost: int = 1) -> bool:
        bucket = self._ensure_bucket(tenant_id, max_per_month)
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(
            bucket["max_tokens"],
            bucket["tokens"] + elapsed * bucket["refill_rate"],
        )
        bucket["last_refill"] = now

        if bucket["tokens"] >= cost:
            bucket["tokens"] -= cost
            return True
        return False

    def remaining(self, tenant_id: str, max_per_month: int) -> int:
        bucket = self._ensure_bucket(tenant_id, max_per_month)
        return max(0, int(bucket["tokens"]))
