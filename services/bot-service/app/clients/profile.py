"""Client for profile-service."""
from __future__ import annotations

from ..config import settings
from .base import get_json, post_json


async def get_my_profile(token: str) -> dict | None:
    try:
        return await get_json(f"{settings.profile_service_url}/profiles/me", token)
    except Exception:
        return None


async def update_profile(token: str, data: dict) -> dict | None:
    """Update profile with partial data (PUT /profiles/me)."""
    try:
        import httpx
        from .base import _TIMEOUT, auth_headers
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.put(
                f"{settings.profile_service_url}/profiles/me",
                headers=auth_headers(token),
                json=data,
            )
            return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None
