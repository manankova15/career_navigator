"""Отправка задач в очередь ingestion-worker (Celery) и чтение их статуса."""

from __future__ import annotations

from typing import Any

from celery import Celery
from celery.result import AsyncResult

from .config import settings

# Один общий Celery-клиент на процесс:
# тот же broker/backend (Redis), что и у ingestion-worker, — поэтому
# AsyncResult умеет получать состояние и результат задач по task_id.
_celery_app = Celery(
    "ingestion",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


def enqueue_fetch_source(
    source_id: str, max_vacancies: int | None = None
) -> str:
    """Поставить в очередь загрузку по одному источнику (см. app.tasks.fetch.fetch_source).

    Возвращает celery task_id, чтобы вызывающая сторона могла опрашивать статус.
    """
    kwargs: dict = {}
    if max_vacancies is not None:
        kwargs["max_vacancies"] = max_vacancies
    async_result = _celery_app.send_task(
        "app.tasks.fetch.fetch_source",
        args=[source_id],
        kwargs=kwargs,
    )
    return async_result.id


def get_job_status(task_id: str) -> dict[str, Any]:
    """Вернуть статус задачи Celery по task_id.

    Celery для неизвестного task_id возвращает state="PENDING" — этого достаточно,
    чтобы фронт показал "задача в очереди" до тех пор, пока воркер её не возьмёт.
    """
    ar: AsyncResult = _celery_app.AsyncResult(task_id)
    state = ar.state or "PENDING"
    payload: dict[str, Any] = {"task_id": task_id, "state": state}

    if state == "SUCCESS":
        result = ar.result
        payload["ready"] = True
        payload["result"] = result if isinstance(result, (dict, list)) else {"value": result}
    elif state == "FAILURE":
        payload["ready"] = True
        payload["error"] = str(ar.result) if ar.result is not None else "Task failed"
    else:
        payload["ready"] = False

    return payload
