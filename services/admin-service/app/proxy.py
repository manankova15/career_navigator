"""
HTTP proxy helpers for calling downstream services.
Передаёт JWT администратора в Authorization — downstream проверяет роль admin.
"""
from __future__ import annotations

import httpx

from .config import settings

_TIMEOUT = httpx.Timeout(30.0)


def _bearer_headers(authorization: str) -> dict[str, str]:
    return {"Authorization": authorization}


async def proxy_get(
    url: str, authorization: str, params: dict | None = None
) -> dict | list:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_bearer_headers(authorization), params=params)
        resp.raise_for_status()
        return resp.json()


async def proxy_patch(url: str, authorization: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.patch(
            url, headers=_bearer_headers(authorization), json=body
        )
        resp.raise_for_status()
        return resp.json()


async def proxy_delete(url: str, authorization: str) -> int:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.delete(url, headers=_bearer_headers(authorization))
        return resp.status_code


async def proxy_post(
    url: str, authorization: str, body: dict | None = None
) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            url, headers=_bearer_headers(authorization), json=body or {}
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {}


# ── Downstream shortcuts ──────────────────────────────────────────────────────


async def get_vacancies(
    authorization: str, page: int = 1, page_size: int = 20, q: str = ""
) -> dict:
    return await proxy_get(
        f"{settings.vacancy_service_url}/vacancies/admin",
        authorization,
        params={"page": page, "page_size": page_size, "q": q},
    )


async def moderate_vacancy(authorization: str, vacancy_id: str, status: str) -> dict:
    return await proxy_patch(
        f"{settings.vacancy_service_url}/vacancies/admin/{vacancy_id}/status",
        authorization,
        body={"status": status},
    )


async def get_sources(authorization: str) -> dict | list:
    return await proxy_get(
        f"{settings.source_service_url}/sources",
        authorization,
        params={"enabled_only": "false"},
    )


async def trigger_source_sync(
    authorization: str,
    source_id: str,
    body: dict | None = None,
) -> dict:
    return await proxy_post(
        f"{settings.source_service_url}/sources/{source_id}/sync",
        authorization,
        body=body or {},
    )


async def get_source_sync_job(authorization: str, task_id: str) -> dict:
    """Проксирование чтения статуса ingestion-задачи по task_id."""
    return await proxy_get(
        f"{settings.source_service_url}/sources/sync/jobs/{task_id}",
        authorization,
    )


async def get_assessments(
    authorization: str, page: int = 1, page_size: int = 20
) -> dict:
    return await proxy_get(
        f"{settings.assessment_service_url}/assessments/admin",
        authorization,
        params={"page": page, "page_size": page_size},
    )


async def publish_assessment(
    authorization: str, assessment_id: str, is_published: bool
) -> dict:
    return await proxy_patch(
        f"{settings.assessment_service_url}/assessments/{assessment_id}",
        authorization,
        body={"is_published": is_published},
    )


async def get_users(
    authorization: str, page: int = 1, page_size: int = 20
) -> dict:
    return await proxy_get(
        f"{settings.auth_service_url}/auth/admin/users",
        authorization,
        params={"page": page, "page_size": page_size},
    )


async def get_auth_admin_stats(authorization: str) -> dict:
    return await proxy_get(
        f"{settings.auth_service_url}/auth/admin/stats",
        authorization,
    )


async def get_assessment_admin_stats(authorization: str) -> dict:
    return await proxy_get(
        f"{settings.assessment_service_url}/assessments/admin/stats",
        authorization,
    )
