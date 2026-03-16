from celery import Celery
from celery.schedules import crontab

from .config import settings

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

celery.conf.beat_schedule = {
    # Fetch hh.ru vacancies every 2 hours
    "fetch-hh-every-2h": {
        "task": "app.tasks.fetch.fetch_all_sources",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # Normalize accumulated raw vacancies every 30 minutes
    "normalize-raw-every-30m": {
        "task": "app.tasks.normalize.normalize_pending_raw",
        "schedule": crontab(minute="*/30"),
    },
    # Deduplication daily at 03:00
    "dedup-daily": {
        "task": "app.tasks.dedup.run_deduplication",
        "schedule": crontab(hour=3, minute=0),
    },
}
