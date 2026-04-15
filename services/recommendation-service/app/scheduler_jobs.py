"""Background jobs for recommendation refresh."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .orchestrator import run_recommendation_from_db_profile

logger = logging.getLogger(__name__)


def run_hourly_recommendation_refresh(db: Session) -> int:
    """
    Refresh recommendations for users whose last session is older than refresh_interval_hours.
    Returns the number of users processed successfully.
    """
    if not settings.enable_scheduled_refresh:
        return 0

    threshold = datetime.utcnow() - timedelta(hours=float(settings.refresh_interval_hours))
    rows = db.execute(
        text(
            """
            WITH last_sess AS (
                SELECT user_id, MAX(created_at) AS la
                FROM recommendation_sessions
                GROUP BY user_id
            )
            SELECT user_id FROM last_sess
            WHERE la < :threshold
            ORDER BY la ASC
            LIMIT :lim
            """
        ),
        {"threshold": threshold, "lim": settings.max_users_per_refresh},
    ).fetchall()

    ok = 0
    for (uid,) in rows:
        try:
            session = run_recommendation_from_db_profile(db, UUID(str(uid)))
            if session is not None:
                ok += 1
        except Exception:
            logger.exception("Scheduled recommendation refresh failed for user_id=%s", uid)
    if rows:
        logger.info("Scheduled refresh: %d users due, %d succeeded", len(rows), ok)
    return ok
