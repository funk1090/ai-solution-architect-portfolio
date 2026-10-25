"""In-process rate limiting (Feature 0010, FR4/FR5).

Two tiers, both keyed by the authenticated API key and applied *after*
authentication, so unauthenticated or malformed requests (401/422) never
create buckets or consume tokens:

- ``default``: every protected request.
- ``expensive``: additionally, routes that call the LLM, the embedding
  model or heavy pipelines (they protect the GPU/process from saturation).

Token bucket: capacity == per-minute limit, refilled continuously. State
is per process (see Feature 0010, Known Limitations). With a single
shared key the limit is effectively global.
"""
from __future__ import annotations

import hashlib
import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from prometheus_client import Counter

from portfolio_api.auth import verify_api_key
from portfolio_api.config import Settings

RATE_LIMITED = Counter(
    "api_rate_limited", "Requests rejected with HTTP 429.", ["tier"]
)


class TokenBucketLimiter:
    """Thread-safe token bucket per key with bounded memory (LRU)."""

    def __init__(
        self,
        per_minute: int,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = 1024,
    ) -> None:
        self._per_minute = per_minute
        self._rate = per_minute / 60.0  # tokens per second
        self._clock = clock
        self._max_keys = max_keys
        self._buckets: OrderedDict[str, tuple[float, float]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._per_minute > 0

    def __len__(self) -> int:
        return len(self._buckets)

    def acquire(self, key: str) -> tuple[bool, float]:
        """Try to take one token. Returns (allowed, seconds_until_retry)."""
        if not self.enabled:
            return True, 0.0
        now = self._clock()
        with self._lock:
            tokens, last = self._buckets.pop(key, (float(self._per_minute), now))
            tokens = min(float(self._per_minute), tokens + (now - last) * self._rate)
            if tokens >= 1.0:
                allowed, retry_after = True, 0.0
                tokens -= 1.0
            else:
                allowed, retry_after = False, (1.0 - tokens) / self._rate
            self._buckets[key] = (tokens, now)
            while len(self._buckets) > self._max_keys:
                self._buckets.popitem(last=False)
        return allowed, retry_after


_limiters: dict[str, TokenBucketLimiter] = {}
_registry_lock = threading.Lock()


def _limit_for(tier: str, settings: Settings) -> int:
    return {
        "default": settings.rate_limit_default_per_minute,
        "expensive": settings.rate_limit_expensive_per_minute,
    }[tier]


def get_limiter(tier: str) -> TokenBucketLimiter:
    with _registry_lock:
        if tier not in _limiters:
            _limiters[tier] = TokenBucketLimiter(_limit_for(tier, Settings()))
        return _limiters[tier]


def reset_limiters() -> None:
    """Forget all buckets and re-read settings on next use (tests)."""
    with _registry_lock:
        _limiters.clear()


def _enforce(tier: str, api_key: str | None) -> None:
    identity = hashlib.sha256((api_key or "anonymous").encode()).hexdigest()[:16]
    allowed, retry_after = get_limiter(tier).acquire(identity)
    if not allowed:
        RATE_LIMITED.labels(tier=tier).inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({tier} tier). Retry later.",
            headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
        )


def limit_default(api_key: str | None = Depends(verify_api_key)) -> None:
    _enforce("default", api_key)


def limit_expensive(api_key: str | None = Depends(verify_api_key)) -> None:
    _enforce("expensive", api_key)
