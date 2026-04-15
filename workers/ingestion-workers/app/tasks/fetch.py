"""
Fetch task: iterates enabled sources, fetches raw vacancies,
persists them to raw_vacancies table.
"""

import logging
import math

from ..celery_app import celery
from ..config import settings
from ..database import get_db_ctx
from ..models import RawVacancy, VacancySource
from ..adapters.hh import fetch_vacancies

logger = logging.getLogger(__name__)


def _effective_max_vacancies(max_vacancies: int | None) -> int:
    if max_vacancies is None:
        return settings.sync_default_max_vacancies
    return min(max(1, max_vacancies), settings.sync_max_vacancies_cap)


@celery.task(name="app.tasks.fetch.fetch_all_sources", bind=True, max_retries=3)
def fetch_all_sources(self):
    """Entry point: fetch all enabled sources."""
    with get_db_ctx() as db:
        sources = db.query(VacancySource).filter(VacancySource.enabled == True).all()  # noqa: E712

    logger.info("Starting fetch for %d enabled sources", len(sources))
    for source in sources:
        fetch_source.delay(str(source.id))


@celery.task(
    name="app.tasks.fetch.fetch_source",
    bind=True,
    max_retries=3,
    soft_time_limit=3300,
    time_limit=3600,
)
def fetch_source(self, source_id: str, max_vacancies: int | None = None):
    """Fetch a single source and persist raw payloads (HH) или canonical (Telegram)."""
    cap = _effective_max_vacancies(max_vacancies)

    with get_db_ctx() as db:
        source = db.query(VacancySource).filter(VacancySource.id == source_id).first()
        if not source or not source.enabled:
            logger.warning("Source %s not found or disabled", source_id)
            return

        cfg = source.config or {}
        source_type = source.source_type
        source_name = source.name

    logger.info(
        "Fetching source=%s type=%s max_vacancies=%s (effective=%d)",
        source_name,
        source_type,
        max_vacancies,
        cap,
    )

    if source_type == "api" and "hh.ru" in source_name.lower():
        _fetch_hh(source_id, cfg, cap)
    elif source_type == "telegram":
        from ..adapters.telegram_fetch import fetch_telegram_source

        fetch_telegram_source(str(source_id), cfg, source_name, cap)
    else:
        logger.warning("No adapter for source_type=%s name=%s", source_type, source_name)


def _fetch_hh(source_id: str, cfg: dict, max_vacancies: int):
    query = cfg.get("default_query", "python")
    area_id = cfg.get("area_id", 1)
    per_page = min(int(cfg.get("per_page", 100)), 100)

    max_pages_setting = settings.fetch_pages_per_run
    pages_for_cap = max(1, math.ceil(max_vacancies / per_page))
    max_pages = min(max_pages_setting, pages_for_cap)

    items = fetch_vacancies(
        query=query,
        area_id=area_id,
        per_page=per_page,
        max_pages=max_pages,
    )

    new_count = 0
    with get_db_ctx() as db:
        for item in items:
            if new_count >= max_vacancies:
                break
            external_id = str(item.get("id", ""))
            if not external_id:
                continue

            exists = (
                db.query(RawVacancy)
                .filter(
                    RawVacancy.source_id == source_id,
                    RawVacancy.external_id == external_id,
                )
                .first()
            )
            if exists:
                continue

            raw = RawVacancy(
                source_id=source_id,
                external_id=external_id,
                canonical_url=item.get("alternate_url", ""),
                payload=item,
            )
            db.add(raw)
            new_count += 1

        db.commit()

    logger.info("hh.ru source=%s: %d new raw vacancies saved (cap=%d)", source_id, new_count, max_vacancies)
