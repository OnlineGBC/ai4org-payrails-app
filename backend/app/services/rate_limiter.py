"""Simple in-memory fixed-window rate limiter.

Per-instance only (state is not shared across Cloud Run instances); adequate as a
first line of abuse prevention. Production should front this with a shared store
(Redis / Memorystore) or an API gateway for global limits.
"""
import time


class FixedWindowRateLimiter:
    def __init__(self):
        self._hits = {}  # key -> (window_start, count)

    def allow(self, key: str, max_requests: int, window_seconds: int, now: float = None) -> bool:
        now = time.time() if now is None else now
        window_start, count = self._hits.get(key, (now, 0))
        if now - window_start >= window_seconds:
            window_start, count = now, 0
        count += 1
        self._hits[key] = (window_start, count)
        return count <= max_requests

    def clear(self) -> None:
        self._hits.clear()


rate_limiter = FixedWindowRateLimiter()
