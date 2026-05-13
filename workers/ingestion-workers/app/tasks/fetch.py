"""
Fetch task: iterates enabled sources, fetches raw vacancies,
persists them to raw_vacancies table.
"""

import logging
import math
from datetime import datetime
from uuid import UUID, uuid4

from ..celery_app import celery
from ..config import settings
from ..database import get_db_ctx
from ..models import IngestionRun, RawVacancy, VacancySource
from ..adapters.hh import fetch_vacancies

logger = logging.getLogger(__name__)


def _effective_max_vacancies(max_vacancies: int | None) -> int:
    if max_vacancies is None:
        return settings.sync_default_max_vacancies
    return min(max(1, max_vacancies), settings.sync_max_vacancies_cap)


def _coerce_uuid(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _create_run_row(
    source_id,
    source_name: str | None,
    source_type: str | None,
    max_vacancies: int,
    task_id: str | None,
) -> UUID:
    """Создать запись в ingestion_runs со статусом 'running' и вернуть её id.

    Любые ошибки записи логируются и не приводят к падению задачи — наличие
    истории запусков считается best-effort.
    """
    run_id = uuid4()
    try:
        with get_db_ctx() as db:
            row = IngestionRun(
                id=run_id,
                source_id=_coerce_uuid(source_id),
                source_name=source_name,
                source_type=source_type,
                task_id=task_id,
                status="running",
                new_vacancies=0,
                max_vacancies=max_vacancies,
                started_at=datetime.utcnow(),
            )
            db.add(row)
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create ingestion_run row: %s", exc)
    return run_id


def _finalize_run(
    run_id: UUID,
    *,
    status: str,
    new_vacancies: int = 0,
    reason: str | None = None,
    error: str | None = None,
) -> None:
    """Закрыть запись в ingestion_runs (статус, время, счётчики)."""
    try:
        with get_db_ctx() as db:
            row = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
            if row is None:
                logger.warning("ingestion_run %s not found for finalize", run_id)
                return
            row.status = status
            row.new_vacancies = int(new_vacancies or 0)
            row.reason = reason
            row.error = error
            row.finished_at = datetime.utcnow()
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to finalize ingestion_run %s: %s", run_id, exc)


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
    """Fetch a single source and persist raw payloads (HH) или canonical (Telegram).

    Возвращает словарь со статистикой запуска, который Celery сохраняет
    в result backend (Redis) — это позволяет админке показывать статус.

    Дополнительно создаёт запись в таблице ``ingestion_runs`` (статус
    running → success/skipped/failed), чтобы админка могла показывать
    историю запусков независимо от Redis result-backend.
    """
    cap = _effective_max_vacancies(max_vacancies)
    task_id = getattr(getattr(self, "request", None), "id", None)

    with get_db_ctx() as db:
        source = db.query(VacancySource).filter(VacancySource.id == source_id).first()
        if not source or not source.enabled:
            logger.warning("Source %s not found or disabled", source_id)
            run_id = _create_run_row(source_id, None, None, cap, task_id)
            _finalize_run(
                run_id,
                status="skipped",
                reason="source_not_found_or_disabled",
            )
            return {
                "source_id": source_id,
                "status": "skipped",
                "reason": "source_not_found_or_disabled",
                "new_vacancies": 0,
                "max_vacancies": cap,
            }

        cfg = source.config or {}
        source_type = source.source_type
        source_name = source.name

    run_id = _create_run_row(source_id, source_name, source_type, cap, task_id)

    logger.info(
        "Fetching source=%s type=%s max_vacancies=%s (effective=%d)",
        source_name,
        source_type,
        max_vacancies,
        cap,
    )

    new_vacancies = 0
    status = "success"
    reason: str | None = None
    try:
        if source_type == "api" and "hh.ru" in source_name.lower():
            new_vacancies = _fetch_hh(source_id, cfg, cap)
        elif source_type == "telegram":
            from ..adapters.telegram_fetch import (
                TelegramSessionNotAuthorizedError,
                fetch_telegram_source,
                resolve_channel_username,
            )
            from ..adapters.telegram_web import fetch_public_channel_web

            try:
                new_vacancies = fetch_telegram_source(
                    str(source_id), cfg, source_name, cap
                )
            except TelegramSessionNotAuthorizedError as exc:
                # Сессия Telethon не авторизована — fallback на публичный
                # web-preview (t.me/s/<channel>). Авторизация не требуется,
                # работает для любого публичного канала.
                logger.warning(
                    "Telegram Telethon session not ready for source=%s: %s "
                    "— пробуем web-preview fallback",
                    source_name,
                    exc,
                )
                channel = resolve_channel_username(cfg, source_name)
                if not channel:
                    status = "skipped"
                    reason = "telegram_channel_username_missing"
                else:
                    try:
                        new_vacancies = fetch_public_channel_web(
                            str(source_id), channel, cap
                        )
                        if new_vacancies == 0:
                            reason = "telegram_web_no_new_messages"
                    except Exception as web_exc:  # noqa: BLE001
                        logger.exception(
                            "Telegram web fallback failed for source=%s: %s",
                            source_name,
                            web_exc,
                        )
                        status = "failed"
                        reason = f"telegram_web_error:{web_exc}"
        else:
            logger.warning(
                "No adapter for source_type=%s name=%s", source_type, source_name
            )
            status = "skipped"
            reason = f"no_adapter_for_type:{source_type}"
    except Exception as exc:
        logger.exception("Fetch failed for source=%s: %s", source_name, exc)
        _finalize_run(
            run_id,
            status="failed",
            new_vacancies=new_vacancies,
            error=str(exc),
        )
        return {
            "source_id": source_id,
            "source_name": source_name,
            "source_type": source_type,
            "status": "failed",
            "error": str(exc),
            "new_vacancies": new_vacancies,
            "max_vacancies": cap,
        }

    _finalize_run(
        run_id,
        status=status,
        new_vacancies=int(new_vacancies or 0),
        reason=reason,
    )

    # Если успех и есть новые сырые вакансии — сразу запускаем нормализацию
    # и затем дедупликацию, чтобы пользователь в админке увидел итог без
    # ручных шагов. Хвост пайплайна работает best-effort: ошибки логируем,
    # но статус самого fetch это не меняет.
    if status == "success" and int(new_vacancies or 0) > 0:
        try:
            from .normalize import normalize_pending_raw
            from .dedup import run_deduplication

            # chain: сначала нормализация, потом дедупликация на canonical-таблице.
            from celery import chain as _celery_chain

            _celery_chain(
                normalize_pending_raw.si(),
                run_deduplication.si(),
            ).apply_async()
            logger.info(
                "post-fetch normalize+dedup chain dispatched for source=%s",
                source_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to dispatch normalize+dedup chain after fetch: %s", exc
            )

    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "status": status,
        "reason": reason,
        "new_vacancies": int(new_vacancies or 0),
        "max_vacancies": cap,
    }


def _hh_queries_from_cfg(cfg: dict) -> list[str]:
    """Поддерживаем оба формата: одиночный default_query и список default_queries."""
    queries_field = cfg.get("default_queries")
    if isinstance(queries_field, list) and queries_field:
        return [str(q).strip() for q in queries_field if str(q).strip()]
    single = cfg.get("default_query")
    if isinstance(single, str) and single.strip():
        # Разбиваем по запятой/| для удобства — но без логики OR.
        parts = [p.strip() for p in single.replace("|", ",").split(",") if p.strip()]
        return parts or [single.strip()]
    return ["python developer"]


def _fetch_hh(source_id: str, cfg: dict, max_vacancies: int) -> int:
    queries = _hh_queries_from_cfg(cfg)
    area_id = cfg.get("area_id", 1)
    # hh.ru разрешает per_page до 100; для уменьшения вероятности 400 на широких
    # запросах берём более скромное значение по умолчанию.
    per_page = min(int(cfg.get("per_page", 50)), 100)

    max_pages_setting = settings.fetch_pages_per_run
    # На каждый отдельный запрос даём свою «долю» страниц — иначе с лимитом
    # max_vacancies=200 и одним коротким запросом ничего не достанется второму.
    per_query_cap = max(1, math.ceil(max_vacancies / max(1, len(queries))))
    pages_for_cap = max(1, math.ceil(per_query_cap / per_page))
    max_pages = min(max_pages_setting, pages_for_cap)

    items: list[dict] = []
    for query in queries:
        try:
            items.extend(
                fetch_vacancies(
                    query=query,
                    area_id=area_id,
                    per_page=per_page,
                    max_pages=max_pages,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "hh.ru query=%r failed (продолжаем со следующим): %s", query, exc
            )

    new_count = 0
    with get_db_ctx() as db:
        seen_external: set[str] = set()
        for item in items:
            if new_count >= max_vacancies:
                break
            external_id = str(item.get("id", ""))
            if not external_id or external_id in seen_external:
                continue
            seen_external.add(external_id)

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

    logger.info(
        "hh.ru source=%s: %d new raw vacancies saved (cap=%d, queries=%d)",
        source_id,
        new_count,
        max_vacancies,
        len(queries),
    )
    return new_count
