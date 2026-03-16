"""Client for vacancy-service."""
from __future__ import annotations

from ..config import settings
from .base import get_json


async def search_vacancies(
    token: str,
    query: str = "",
    location: str | None = None,
    seniority: str | None = None,
    limit: int = 5,
) -> list[dict]:
    params: dict = {"page_size": limit, "page": 1}
    if query:
        params["q"] = query
    if location:
        params["location"] = location
    if seniority:
        params["seniority"] = seniority
    try:
        data = await get_json(
            f"{settings.vacancy_service_url}/vacancies",
            token,
            params=params,
        )
        return data.get("items", [])
    except Exception:
        return []
