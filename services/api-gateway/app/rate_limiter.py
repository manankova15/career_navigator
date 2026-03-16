"""Simple in-memory rate limiter (sliding window)."""
from __future__ import annotations
import time
from collections import defaultdict, deque
from .config import settings

_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    now = time.time()
    window = _windows[client_ip]

    # Drop timestamps outside the window
    cutoff = now - settings.rate_limit_window_seconds
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) >= settings.rate_limit_requests:
        return False

    window.append(now)
    return True
