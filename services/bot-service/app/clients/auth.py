"""Client for auth-service."""
from __future__ import annotations

import httpx

from ..config import settings
from .base import _TIMEOUT


async def login(email: str, password: str) -> dict | None:
    """Return {access_token, refresh_token} or None on bad credentials."""
    url = f"{settings.auth_service_url}/auth/login"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json={"email": email, "password": password})
            if resp.status_code == 200:
                return resp.json()
            return None
    except httpx.RequestError:
        return None


async def login_by_telegram(
    telegram_id: int,
    telegram_username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> dict | None:
    """Вход по Telegram: возвращает {access_token, refresh_token} или None. При первом заходе создаётся пользователь."""
    url = f"{settings.auth_service_url}/auth/telegram-login"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                json={
                    "telegram_id": str(telegram_id),
                    "telegram_username": telegram_username,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            return None
    except httpx.RequestError:
        return None


async def register(full_name: str, email: str, password: str) -> dict | None:
    """Return {access_token, refresh_token} or None on failure."""
    url = f"{settings.auth_service_url}/auth/register"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url, json={"full_name": full_name, "email": email, "password": password}
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return None
    except httpx.RequestError:
        return None


async def get_me(token: str) -> dict | None:
    url = f"{settings.auth_service_url}/auth/me"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json()
            return None
    except httpx.RequestError:
        return None


async def link_telegram(token: str, telegram_id: int, telegram_username: str | None) -> bool:
    url = f"{settings.auth_service_url}/auth/link-telegram"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "telegram_id": str(telegram_id),
                    "telegram_username": telegram_username or "",
                },
            )
            return resp.status_code == 200
    except httpx.RequestError:
        return False
