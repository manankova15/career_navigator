"""
Fetch task: iterates enabled sources, fetches raw vacancies,
persists them to raw_vacancies table.
"""

import logging

from ..celery_app import celery
from ..database import get_db_ctx
from ..models import RawVacancy, VacancySource
from ..adapters.hh import fetch_vacancies

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.fetch.fetch_all_sources", bind=True, max_retries=3)
def fetch_all_sources(self):
    """Entry point: fetch all enabled sources."""
    with get_db_ctx() as db:
        sources = db.query(VacancySource).filter(VacancySource.enabled == True).all()  # noqa: E712

    logger.info("Starting fetch for %d enabled sources", len(sources))
    for source in sources:
        fetch_source.delay(str(source.id))


@celery.task(name="app.tasks.fetch.fetch_source", bind=True, max_retries=3)
def fetch_source(self, source_id: str):
    """Fetch a single source and persist raw payloads."""
    with get_db_ctx() as db:
        source = db.query(VacancySource).filter(VacancySource.id == source_id).first()
        if not source or not source.enabled:
            logger.warning("Source %s not found or disabled", source_id)
            return

        cfg = source.config or {}
        source_type = source.source_type
        source_name = source.name

    logger.info("Fetching source=%s type=%s", source_name, source_type)

    if source_type == "api" and "hh.ru" in source_name.lower():
        _fetch_hh(source_id, cfg)
    else:
        logger.warning("No adapter for source_type=%s name=%s", source_type, source_name)


def _fetch_hh(source_id: str, cfg: dict):
    query = cfg.get("default_query", "python")
    area_id = cfg.get("area_id", 1)
    per_page = cfg.get("per_page", 100)

    from ..config import settings
    items = fetch_vacancies(
        query=query,
        area_id=area_id,
        per_page=min(per_page, 100),
        max_pages=settings.fetch_pages_per_run,
    )

    new_count = 0
    with get_db_ctx() as db:
        for item in items:
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

    logger.info("hh.ru source=%s: %d new raw vacancies saved", source_id, new_count)
