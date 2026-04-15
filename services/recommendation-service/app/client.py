"""
HTTP clients for downstream services.
All calls are synchronous (httpx sync) to keep the service simple.
"""

import json
from typing import Any
from uuid import UUID

import httpx

from .config import settings


def _headers_bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _headers_internal() -> dict[str, str]:
    return {"X-Internal-Token": settings.internal_token}


# ── profile-service ───────────────────────────────────────────────────────────

def fetch_user_profile(user_token: str) -> dict[str, Any]:
    """GET /profiles/me — returns the full profile (preferences + skills)."""
    resp = httpx.get(
        f"{settings.profile_service_url}/profiles/me",
        headers=_headers_bearer(user_token),
        timeout=10,
    )
    resp.raise_for_status()
    profile = resp.json()

    # Also fetch skills
    skills_resp = httpx.get(
        f"{settings.profile_service_url}/profiles/me/skills",
        headers=_headers_bearer(user_token),
        timeout=10,
    )
    skills_resp.raise_for_status()

    # Fetch preferences
    prefs_resp = httpx.get(
        f"{settings.profile_service_url}/profiles/me/preferences",
        headers=_headers_bearer(user_token),
        timeout=10,
    )
    prefs_resp.raise_for_status()

    profile["skills"] = [s["skill_name"] for s in skills_resp.json()]
    profile["preferences"] = prefs_resp.json() or {}
    return profile


# ── vacancy-service ───────────────────────────────────────────────────────────

def fetch_candidate_vacancies(
    location: str | None = None,
    page_size: int = 300,
) -> list[dict[str, Any]]:
    """GET /vacancies — fetch active vacancies for scoring."""
    params: dict[str, Any] = {"status": "active", "page_size": min(page_size, 100), "page": 1}
    if location:
        params["location"] = location

    all_items: list[dict[str, Any]] = []
    for page in range(1, (page_size // 100) + 2):
        params["page"] = page
        resp = httpx.get(
            f"{settings.vacancy_service_url}/vacancies",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        all_items.extend(data.get("items", []))
        if page >= data.get("pages", 1):
            break
        if len(all_items) >= page_size:
            break

    return all_items[:page_size]


# ── ml-service ────────────────────────────────────────────────────────────────

def call_scoring(payload: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{settings.ml_service_url}/ml/score",
        json=payload,
        headers=_headers_internal(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def call_skill_gap(payload: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{settings.ml_service_url}/ml/skill-gap",
        json=payload,
        headers=_headers_internal(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _json_default(obj: Any) -> Any:
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError


def call_rank(payload: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{settings.ml_service_url}/ml/rank",
        content=json.dumps(payload, default=_json_default),
        headers={**_headers_internal(), "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()
