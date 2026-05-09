"""
hh.ru public API adapter.
Docs: https://api.hh.ru/openapi/redoc
No auth required for vacancy search.
"""

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import settings
from ..vacancy_norm import enrich_hh_canonical

logger = logging.getLogger(__name__)


class HHApiError(RuntimeError):
    """Ошибка обращения к публичному API hh.ru с человекочитаемым описанием."""


class _TransientHHError(RuntimeError):
    """5xx/сетевые ошибки — retry'им их, не показывая пользователю промежуточные попытки."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TransportError, httpx.TimeoutException, _TransientHHError)
    ),
    reraise=True,
)
def _get_raw(url: str, params: dict) -> httpx.Response:
    """GET к hh.ru с retry только на транзитные сбои (4xx retry'ить смысла нет)."""
    with httpx.Client(
        base_url=settings.hh_api_base,
        headers={"User-Agent": settings.hh_user_agent},
        timeout=15,
    ) as client:
        response = client.get(url, params=params)
    if 500 <= response.status_code < 600:
        raise _TransientHHError(
            f"hh.ru {response.status_code} {response.reason_phrase}"
        )
    return response


def _get(url: str, params: dict) -> dict:
    try:
        response = _get_raw(url, params)
    except _TransientHHError as exc:
        raise HHApiError(
            f"hh.ru недоступен после нескольких попыток: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise HHApiError(f"hh.ru не ответил вовремя: {exc}") from exc
    except httpx.TransportError as exc:
        raise HHApiError(f"Сетевая ошибка при обращении к hh.ru: {exc}") from exc

    if response.status_code >= 400:
        body = (response.text or "")[:300]
        raise HHApiError(
            f"hh.ru вернул {response.status_code} {response.reason_phrase} "
            f"для {response.request.method} {response.request.url}: {body}"
        )
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
