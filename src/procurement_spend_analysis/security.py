from __future__ import annotations

import threading
import time
from pathlib import Path
import re


SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ALLOWED_UPLOAD_SUFFIXES = {".csv"}


def sanitize_filename(filename: str) -> str:
    original = filename.strip()
    candidate = Path(original).name.strip()
    if candidate != original or any(separator in original for separator in ("/", "\\")):
        raise ValueError("Unsafe filename detected.")
    if not candidate or not SAFE_FILENAME_RE.match(candidate):
        raise ValueError("Unsafe filename detected.")
    if Path(candidate).suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ValueError("Only CSV uploads are supported.")
    return candidate


def validate_text_payload(text: str, max_chars: int = 5_000_000) -> None:
    if len(text) > max_chars:
        raise ValueError("Payload exceeds allowed text size.")
    if "\x00" in text:
        raise ValueError("Payload contains null bytes.")


class IPRateLimiter:
    """Token-bucket rate limiter keyed by client IP address.

    Use on unauthenticated public write endpoints where JWT / API-key
    rate limiting is not available.  Thread-safe via an internal lock.
    """

    def __init__(self, *, rate_per_minute: int = 30) -> None:
        self._capacity = float(rate_per_minute)
        self._rate = rate_per_minute / 60.0  # tokens per second
        self._buckets: dict[str, tuple[float, float]] = {}  # ip -> (tokens, ts)
        self._lock = threading.Lock()

    def check(self, ip: str) -> None:
        """Consume one token for *ip*.  Raises ``ValueError`` when exhausted."""
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(ip, (self._capacity, now))
            tokens = min(self._capacity, tokens + (now - last) * self._rate)
            if tokens < 1.0:
                raise ValueError("rate limit exceeded")
            self._buckets[ip] = (tokens - 1.0, now)
