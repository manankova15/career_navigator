"""
hh.ru public API adapter.
Docs: https://api.hh.ru/openapi/redoc
No auth required for vacancy search.
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)

HH_SENIORITY_MAP = {
    "noExperience": "intern",
    "between1And3": "junior",
    "between3And6": "middle",
    "moreThan6": "senior",
}

HH_EMPLOYMENT_MAP = {
    "full": "full-time",
    "part": "part-time",
    "project": "project",
    "volunteer": "volunteer",
    "probation": "probation",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _get(url: str, params: dict) -> dict:
    with httpx.Client(
        base_url=settings.hh_api_base,
        headers={"User-Agent": settings.hh_user_agent},
        timeout=15,
    ) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def fetch_vacancies(
    query: str,
    area_id: int = 1,
    per_page: int = 100,
    max_pages: int = 5,
) -> list[dict[str, Any]]:
    """Fetch vacancy list pages from hh.ru."""
    results = []
    for page in range(max_pages):
        logger.info("hh.ru fetch page=%d query=%r area=%d", page, query, area_id)
        data = _get(
            "/vacancies",
            params={
                "text": query,
                "area": area_id,
                "per_page": per_page,
                "page": page,
                "only_with_salary": False,
            },
        )
        items = data.get("items", [])
        results.extend(items)
        if page >= data.get("pages", 1) - 1:
            break
    logger.info("hh.ru fetched %d vacancies total", len(results))
    return results


def normalize_hh_item(item: dict[str, Any], source_id: str) -> dict[str, Any]:
    """Convert a single hh.ru vacancy item to canonical shape."""
    salary = item.get("salary") or {}
    experience = item.get("experience") or {}
    employment = item.get("employment") or {}
    employer = item.get("employer") or {}
    area = item.get("area") or {}
    snippet = item.get("snippet") or {}

    skills = [s["name"] for s in (item.get("key_skills") or [])]

    # Combine snippet for description when full description isn't fetched
    description_parts = filter(None, [
        snippet.get("requirement"),
        snippet.get("responsibility"),
    ])
    description = "\n".join(description_parts) or None

    published_at = None
    if item.get("published_at"):
        try:
            published_at = datetime.fromisoformat(item["published_at"])
        except ValueError:
            pass

    return {
        "source_id": source_id,
        "external_id": str(item["id"]),
        "title": item.get("name", ""),
        "company": employer.get("name", ""),
        "canonical_url": item.get("alternate_url", ""),
        "location": area.get("name"),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency", "RUB"),
        "seniority": HH_SENIORITY_MAP.get(experience.get("id", ""), None),
        "employment_type": HH_EMPLOYMENT_MAP.get(employment.get("id", ""), None),
        "description": description,
        "skills": skills,
        "status": "active",
        "published_at": published_at,
    }
