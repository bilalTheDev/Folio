"""In-process IP rate limiting for auth-free endpoints."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

_lock = Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(headers: dict[str, str], fallback: str = "unknown") -> str:
    forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = headers.get("x-real-ip") or headers.get("X-Real-IP")
    return real_ip or fallback


def allow_request(
    key: str,
    *,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds)."""
    now = time.time()
    with _lock:
        bucket = _hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = int(window_seconds - (now - bucket[0])) + 1
            return False, max(retry, 1)
        bucket.append(now)
        return True, 0
