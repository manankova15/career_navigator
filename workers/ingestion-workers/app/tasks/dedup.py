"""
Deduplication task: uses PostgreSQL pg_trgm similarity to find
near-duplicate canonical vacancies and logs them.
"""

import logging

from sqlalchemy import text

from ..celery_app import celery
from ..config import settings
from ..database import get_db_ctx
from ..models import CanonicalVacancy, DeduplicationLog

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.dedup.run_deduplication", bind=True)
def run_deduplication(self):
    """
    Find pairs of active canonical vacancies with high title+company similarity
    (using pg_trgm) and record them in dedup_log.
    Duplicates older than the primary are archived.
    """
    threshold = settings.dedup_similarity_threshold

    find_duplicates_sql = text("""
        SELECT a.id AS primary_id,
               b.id AS duplicate_id,
               similarity(a.title || ' ' || a.company, b.title || ' ' || b.company) AS sim
        FROM canonical_vacancies a
        JOIN canonical_vacancies b
          ON a.id <> b.id
         AND a.source_id = b.source_id
         AND a.created_at <= b.created_at
         AND b.status = 'active'
         AND similarity(a.title || ' ' || a.company, b.title || ' ' || b.company) >= :threshold
        WHERE a.status = 'active'
        LIMIT 500
    """)

    with get_db_ctx() as db:
        rows = db.execute(find_duplicates_sql, {"threshold": threshold}).fetchall()
        logger.info("Deduplication: found %d candidate pairs", len(rows))

        new_pairs = 0
        archived = 0

        for row in rows:
            primary_id, duplicate_id, sim = row

            already_logged = (
                db.query(DeduplicationLog)
                .filter(
                    DeduplicationLog.primary_vacancy_id == primary_id,
                    DeduplicationLog.duplicate_vacancy_id == duplicate_id,
                )
                .first()
            )
            if already_logged:
                continue

            db.add(DeduplicationLog(
                primary_vacancy_id=primary_id,
                duplicate_vacancy_id=duplicate_id,
                similarity_score=float(sim),
            ))

            dup = db.query(CanonicalVacancy).filter(CanonicalVacancy.id == duplicate_id).first()
            if dup and dup.status == "active":
                dup.status = "archived"
                archived += 1

            new_pairs += 1

        db.commit()

    logger.info(
        "Deduplication complete: %d new pairs logged, %d vacancies archived",
        new_pairs, archived,
    )
