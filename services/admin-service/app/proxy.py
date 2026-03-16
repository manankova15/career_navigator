"""
HTTP proxy helpers for calling downstream services.
Admin-service forwards requests using its internal token so it can
manage resources owned by other services.
"""
from __future__ import annotations

import httpx

from .config import settings

_TIMEOUT = httpx.Timeout(15.0)


def _int_headers() -> dict[str, str]:
    return {"X-Internal-Token": settings.internal_token}


def _bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def proxy_get(url: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_int_headers(), params=params)
        resp.raise_for_status()
        return resp.json()


async def proxy_patch(url: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.patch(url, headers=_int_headers(), json=body)
        resp.raise_for_status()
        return resp.json()


async def proxy_delete(url: str) -> int:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.delete(url, headers=_int_headers())
        return resp.status_code


async def proxy_post(url: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, headers=_int_headers(), json=body)
        resp.raise_for_status()
        return resp.json()


# ── Downstream shortcuts ──────────────────────────────────────────────────────

async def get_vacancies(page: int = 1, page_size: int = 20, q: str = "") -> dict:
    return await proxy_get(
        f"{settings.vacancy_service_url}/vacancies/admin",
        params={"page": page, "page_size": page_size, "q": q},
    )


async def moderate_vacancy(vacancy_id: str, status: str) -> dict:
    return await proxy_patch(
        f"{settings.vacancy_service_url}/vacancies/admin/{vacancy_id}/status",
        body={"status": status},
    )


async def get_sources(page: int = 1, page_size: int = 20) -> dict:
    return await proxy_get(
        f"{settings.source_service_url}/sources",
        params={"page": page, "page_size": page_size},
    )


async def trigger_source_sync(source_id: str) -> dict:
    return await proxy_post(
        f"{settings.source_service_url}/sources/{source_id}/sync",
        body={},
    )


async def get_assessments(page: int = 1, page_size: int = 20) -> dict:
    return await proxy_get(
        f"{settings.assessment_service_url}/assessments/admin",
        params={"page": page, "page_size": page_size},
    )


async def publish_assessment(assessment_id: str, is_published: bool) -> dict:
    return await proxy_patch(
        f"{settings.assessment_service_url}/assessments/{assessment_id}",
        body={"is_published": is_published},
    )


async def get_users(page: int = 1, page_size: int = 20) -> dict:
    return await proxy_get(
        f"{settings.auth_service_url}/auth/admin/users",
        params={"page": page, "page_size": page_size},
    )
