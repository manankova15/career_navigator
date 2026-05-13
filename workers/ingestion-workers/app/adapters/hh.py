"""
hh.ru public API: https://api.hh.ru/openapi/redoc

С ~2025 поиск /vacancies часто требует OAuth (Bearer); анонимно — стабильный 403
forbidden (не «капча по IP»)

Токен: dev.hh.ru → HH_CLIENT_ID/SECRET → client_credentials; HH_AUTH_TOKEN в Authorization
User-Agent с контактом обязателен (документация HH general#user-agent)
"""

import logging
import threading
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


# ── OAuth: ленивое получение и обновление application access-token ──────────
_token_lock = threading.Lock()
_cached_token: str | None = None


def _initial_token() -> str | None:
    return settings.hh_auth_token or None


_cached_token = _initial_token()


def _request_application_token() -> str:
    """grant_type=client_credentials — токен приложения без участия пользователя."""
    if not settings.hh_client_id or not settings.hh_client_secret:
        raise HHApiError(
            "HH вернул 403 (нужен OAuth-токен), но HH_CLIENT_ID/HH_CLIENT_SECRET "
            "не заданы. Заполните их в .env (приложение регистрируется на "
            "https://dev.hh.ru/admin) или передайте готовый HH_AUTH_TOKEN."
        )
    logger.info("HH: запрашиваю новый application access-token")
    try:
        resp = httpx.post(
            f"{settings.hh_api_base}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.hh_client_id,
                "client_secret": settings.hh_client_secret,
            },
            headers={
                "User-Agent": settings.hh_user_agent,
                "HH-User-Agent": settings.hh_user_agent,
            },
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise HHApiError(f"Не удалось получить токен HH: {exc}") from exc
    if resp.status_code != 200:
        raise HHApiError(
            f"HH /token вернул {resp.status_code}: {(resp.text or '')[:300]}"
        )
    token = resp.json().get("access_token")
    if not token:
        raise HHApiError(f"HH /token не вернул access_token: {resp.text[:300]}")
    return token


def _ensure_token(force_refresh: bool = False) -> str | None:
    """Возвращает кэшированный access-token, при необходимости запрашивает новый."""
    global _cached_token
    if not force_refresh and _cached_token:
        return _cached_token
    # Если client_id/secret не заданы — работаем «как есть» (анонимно или со
    # статичным HH_AUTH_TOKEN). Force-refresh без секретов бессмыслен.
    if not settings.hh_client_id or not settings.hh_client_secret:
        return _cached_token
    with _token_lock:
        if force_refresh or not _cached_token:
            _cached_token = _request_application_token()
    return _cached_token


def _build_headers(token: str | None) -> dict[str, str]:
    headers = {
        "User-Agent": settings.hh_user_agent,
        # HH с 2024-го отдельно валидирует HH-User-Agent (см. their docs).
        "HH-User-Agent": settings.hh_user_agent,
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TransportError, httpx.TimeoutException, _TransientHHError)
    ),
    reraise=True,
)
def _get_raw(url: str, params: dict, token: str | None) -> httpx.Response:
    """GET к hh.ru с retry только на транзитные сбои (4xx retry'ить смысла нет)."""
    with httpx.Client(
        base_url=settings.hh_api_base,
        headers=_build_headers(token),
        timeout=15,
    ) as client:
        response = client.get(url, params=params)
    if 500 <= response.status_code < 600:
        raise _TransientHHError(
            f"hh.ru {response.status_code} {response.reason_phrase}"
        )
    return response


def _get(url: str, params: dict) -> dict:
    token = _ensure_token()
    try:
        response = _get_raw(url, params, token)
    except _TransientHHError as exc:
        raise HHApiError(
            f"hh.ru недоступен после нескольких попыток: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise HHApiError(f"hh.ru не ответил вовремя: {exc}") from exc
    except httpx.TransportError as exc:
        raise HHApiError(f"Сетевая ошибка при обращении к hh.ru: {exc}") from exc

    # 403: либо токен протух, либо его вообще нет → пробуем перевыпустить
    # (если заданы client_id/secret) и повторить запрос ровно один раз.
    if response.status_code == 403 and settings.hh_client_id and settings.hh_client_secret:
        logger.warning(
            "HH ответил 403 на %s — пробую перевыпустить application access-token и повторить",
            url,
        )
        try:
            new_token = _ensure_token(force_refresh=True)
            response = _get_raw(url, params, new_token)
        except (_TransientHHError, httpx.HTTPError) as exc:
            raise HHApiError(
                f"hh.ru не принял запрос даже после перевыпуска токена: {exc}"
            ) from exc

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
    """Fetch vacancy list pages from hh.ru.

    Hh.ru ограничивает per_page <= 100 и иногда возвращает 400 для слишком
    «жадных» запросов или сочетаний параметров (например, only_with_salary
    как строка False). Поэтому шлём только необходимые поля.
    """
    # Защитимся от случайно подсунутого per_page > 100.
    safe_per_page = min(max(1, int(per_page)), 100)
    results: list[dict[str, Any]] = []
    for page in range(max_pages):
        logger.info(
            "hh.ru fetch page=%d query=%r area=%s per_page=%d",
            page,
            query,
            area_id,
            safe_per_page,
        )
        params: dict[str, Any] = {
            "text": query,
            "per_page": safe_per_page,
            "page": page,
        }
        # area опциональна: без неё API ищет по всем регионам, что тоже валидно.
        if area_id is not None:
            params["area"] = int(area_id)
        data = _get("/vacancies", params=params)
        items = data.get("items", [])
        results.extend(items)
        if page >= data.get("pages", 1) - 1:
            break
    logger.info("hh.ru fetched %d vacancies total", len(results))
    return results


def normalize_hh_item(item: dict[str, Any], source_id: str, source_name: str = "hh") -> dict[str, Any]:
    """Convert a single hh.ru vacancy item to canonical shape (нормализованные поля по ТЗ)."""
    return enrich_hh_canonical(item, source_id, source_name)
