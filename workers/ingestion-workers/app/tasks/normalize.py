"""
Normalize task: reads unprocessed raw_vacancies, converts them
to canonical format, upserts into canonical_vacancies.
"""

import logging
from datetime import datetime

from ..celery_app import celery
from ..database import get_db_ctx
from ..models import CanonicalVacancy, RawVacancy, VacancySource
from ..adapters.hh import normalize_hh_item

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


@celery.task(name="app.tasks.normalize.normalize_pending_raw", bind=True)
def normalize_pending_raw(self):
    """Convert all unprocessed raw vacancies to canonical form."""
    with get_db_ctx() as db:
        raws = (
            db.query(RawVacancy)
            .filter(RawVacancy.processed == False)  # noqa: E712
            .limit(BATCH_SIZE)
            .all()
        )

    logger.info("Normalizing %d raw vacancies", len(raws))
    ok = err = 0
    for raw in raws:
        try:
            normalize_single.delay(str(raw.id))
            ok += 1
        except Exception as exc:
            logger.error("Failed to dispatch normalize for raw=%s: %s", raw.id, exc)
            err += 1

    logger.info("Dispatched normalize tasks: ok=%d err=%d", ok, err)


@celery.task(name="app.tasks.normalize.normalize_single", bind=True, max_retries=3)
def normalize_single(self, raw_id: str):
    """Normalize a single raw vacancy."""
    import uuid

    with get_db_ctx() as db:
        raw = db.query(RawVacancy).filter(RawVacancy.id == raw_id).first()
        if not raw:
            logger.warning("RawVacancy %s not found", raw_id)
            return

        source = db.query(VacancySource).filter(VacancySource.id == raw.source_id).first()
        source_name = source.name if source else ""

    try:
        if "hh.ru" in source_name.lower():
            canonical_data = normalize_hh_item(raw.payload, str(raw.source_id))
        else:
            logger.warning("No normalizer for source %s", source_name)
            _mark_processed(raw_id)
            return

        with get_db_ctx() as db:
            existing = (
                db.query(CanonicalVacancy)
                .filter(
                    CanonicalVacancy.source_id == canonical_data["source_id"],
                    CanonicalVacancy.external_id == canonical_data["external_id"],
                )
                .first()
            )

            if existing:
                for key, value in canonical_data.items():
                    if value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                vacancy = CanonicalVacancy(**canonical_data)
                db.add(vacancy)

            db.commit()

        _mark_processed(raw_id)
        logger.debug("Normalized raw=%s → canonical %s", raw_id, canonical_data["external_id"])

    except Exception as exc:
        logger.error("Error normalizing raw=%s: %s", raw_id, exc, exc_info=True)
        raise self.retry(exc=exc)


def _mark_processed(raw_id: str):
    with get_db_ctx() as db:
        raw = db.query(RawVacancy).filter(RawVacancy.id == raw_id).first()
        if raw:
            raw.processed = True
            db.commit()
