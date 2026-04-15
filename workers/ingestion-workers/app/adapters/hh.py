"""
hh.ru public API adapter.
Docs: https://api.hh.ru/openapi/redoc
No auth required for vacancy search.
"""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..vacancy_norm import enrich_hh_canonical

logger = logging.getLogger(__name__)


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


def normalize_hh_item(item: dict[str, Any], source_id: str, source_name: str = "hh") -> dict[str, Any]:
    """Convert a single hh.ru vacancy item to canonical shape (нормализованные поля по ТЗ)."""
    return enrich_hh_canonical(item, source_id, source_name)
