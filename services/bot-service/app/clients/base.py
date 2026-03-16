"""Shared HTTP client helpers."""
from __future__ import annotations

import httpx

from ..config import settings

_TIMEOUT = httpx.Timeout(10.0, read=15.0)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def internal_headers() -> dict[str, str]:
    return {"X-Internal-Token": settings.internal_token}


async def get_json(url: str, token: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=auth_headers(token), params=params)
        resp.raise_for_status()
        return resp.json()


async def post_json(url: str, token: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, headers=auth_headers(token), json=body)
        resp.raise_for_status()
        return resp.json()


async def post_internal(url: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, headers=internal_headers(), json=body)
        resp.raise_for_status()
        return resp.json()
