"""Simple in-memory rate limiter (sliding window)."""
from __future__ import annotations
import time
from collections import defaultdict, deque
from .config import settings

_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(client_key: str, *, limit: int | None = None, window_seconds: int | None = None) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    now = time.time()
    max_requests = limit if limit is not None else settings.rate_limit_requests
    window_size = window_seconds if window_seconds is not None else settings.rate_limit_window_seconds
    window = _windows[client_key]

    # Drop timestamps outside the window
    cutoff = now - window_size
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) >= max_requests:
        return False

    window.append(now)
    return True
