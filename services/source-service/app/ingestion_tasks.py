"""Отправка задач в очередь ingestion-worker (Celery)."""

from celery import Celery

from .config import settings


def enqueue_fetch_source(source_id: str, max_vacancies: int | None = None) -> None:
    """Поставить в очередь загрузку по одному источнику (см. app.tasks.fetch.fetch_source)."""
    app = Celery(
        "ingestion",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    kwargs: dict = {}
    if max_vacancies is not None:
        kwargs["max_vacancies"] = max_vacancies
    app.send_task("app.tasks.fetch.fetch_source", args=[source_id], kwargs=kwargs)
