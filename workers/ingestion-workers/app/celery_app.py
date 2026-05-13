"""
Celery-приложение ingestion-worker.

Beat-расписание подгружается из таблицы system_settings (ключ
`ingestion_schedule`), чтобы админ мог менять частоту автоматической дозагрузки
из админ-панели без передеплоя контейнеров. При отсутствии настройки или
ошибках чтения БД используются безопасные дефолты.
"""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import beat_init

from .config import settings

logger = logging.getLogger(__name__)

DEFAULT_FETCH_INTERVAL_HOURS = 2
DEFAULT_NORMALIZE_INTERVAL_MINUTES = 30

celery = Celery(
    "ingestion",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.fetch",
        "app.tasks.normalize",
        "app.tasks.dedup",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _load_schedule_from_db() -> tuple[int, int]:
    """Возвращает (fetch_interval_hours, normalize_interval_minutes).

    Если таблицы ещё нет или запись отсутствует — отдаём дефолты.
    """
    try:
        # Импортируем лениво — на время сборки контейнера/первого запуска БД
        # может ещё не существовать.
        from sqlalchemy import text

        from .database import engine

        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT value FROM system_settings WHERE key = :k"
                ),
                {"k": "ingestion_schedule"},
            ).fetchone()
        if row is None:
            return DEFAULT_FETCH_INTERVAL_HOURS, DEFAULT_NORMALIZE_INTERVAL_MINUTES
        value = row[0] or {}
        fh = int(value.get("fetch_interval_hours", DEFAULT_FETCH_INTERVAL_HOURS))
        nm = int(value.get("normalize_interval_minutes", DEFAULT_NORMALIZE_INTERVAL_MINUTES))
        # Sanity bounds.
        fh = max(1, min(fh, 168))
        nm = max(5, min(nm, 1440))
        return fh, nm
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Не удалось загрузить ingestion_schedule из БД, используем дефолты: %s",
            exc,
        )
        return DEFAULT_FETCH_INTERVAL_HOURS, DEFAULT_NORMALIZE_INTERVAL_MINUTES


def _build_beat_schedule() -> dict:
    fetch_hours, normalize_minutes = _load_schedule_from_db()
    hour_spec = "*" if fetch_hours == 1 else f"*/{fetch_hours}"
    minute_spec = "*" if normalize_minutes == 1 else f"*/{normalize_minutes}"
    return {
        "fetch-all-sources": {
            "task": "app.tasks.fetch.fetch_all_sources",
            "schedule": crontab(minute=0, hour=hour_spec),
        },
        "normalize-raw": {
            "task": "app.tasks.normalize.normalize_pending_raw",
            "schedule": crontab(minute=minute_spec),
        },
        "dedup-daily": {
            "task": "app.tasks.dedup.run_deduplication",
            "schedule": crontab(hour=3, minute=0),
        },
    }


celery.conf.beat_schedule = _build_beat_schedule()


@beat_init.connect
def _reload_schedule_on_beat_start(sender=None, **kwargs):  # noqa: ANN001, D401
    """При старте beat'а перечитываем расписание (актуально после миграций)."""
    try:
        sender.app.conf.beat_schedule = _build_beat_schedule()
    except Exception as exc:  # noqa: BLE001
        logger.warning("beat_init reload failed: %s", exc)
