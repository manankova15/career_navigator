"""
Загрузка вакансий из одного Telegram-канала (Telethon) → vacancy-service /internal/canonical.
Логика парсинга сообщений — telegram_parse (как в scripts/seed_telegram_vacancies.py).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ..config import settings
from ..internal_jwt import make_admin_access_token
from ..telegram_parse import parse_message

logger = logging.getLogger(__name__)


def resolve_channel_username(cfg: dict[str, Any], source_name: str) -> str | None:
    ch = (cfg.get("channel_username") or cfg.get("channel") or "").strip().lstrip("@")
    if ch:
        return ch
    lower = source_name.lower()
    for prefix in ("tg:", "tg ", "telegram:", "telegram ", "telegram/"):
        if lower.startswith(prefix):
            return source_name[len(prefix) :].strip().lstrip("/").lstrip("@")
    return None


def _post_canonical(payload: dict[str, Any]) -> bool:
    url = f"{settings.vacancy_service_url.rstrip('/')}/internal/canonical"
    token = make_admin_access_token()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code in (200, 201):
            return True
        logger.warning(
            "vacancy canonical POST failed status=%s body=%s",
            resp.status_code,
            (resp.text or "")[:300],
        )
        return False
    except Exception as exc:
        logger.error("vacancy canonical POST error: %s", exc)
        return False


async def _fetch_telegram_async(
    source_uuid: str,
    channel: str,
    max_new: int,
) -> int:
    try:
        from telethon import TelegramClient
    except ImportError as exc:
        raise RuntimeError("Пакет telethon не установлен в ingestion-worker") from exc

    api_id = (settings.telegram_api_id or "").strip()
    api_hash = (settings.telegram_api_hash or "").strip()
    if not api_id or not api_hash:
        raise RuntimeError(
            "Не заданы TELEGRAM_API_ID / TELEGRAM_API_HASH для загрузки из Telegram"
        )

    session_path = settings.telegram_session_file
    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.start()

    loaded = 0
    skipped = 0
    offset_id = 0
    batch_size = settings.telegram_batch_size
    delay = settings.telegram_request_delay_seconds

    try:
        while loaded < max_new:
            batch = await client.get_messages(
                f"@{channel}",
                limit=batch_size,
                offset_id=offset_id,
            )
            if not batch:
                break

            for msg in batch:
                text = msg.text or msg.message or ""
                if not text:
                    continue
                vacancy = parse_message(
                    msg.id, text, msg.date, channel, source_uuid
                )
                if vacancy is None:
                    skipped += 1
                    continue
                if _post_canonical(vacancy):
                    loaded += 1
                    logger.info(
                        "tg channel=%s loaded=%d/%d external=%s",
                        channel,
                        loaded,
                        max_new,
                        vacancy.get("external_id"),
                    )
                else:
                    skipped += 1

                if loaded >= max_new:
                    break

            offset_id = batch[-1].id
            await asyncio.sleep(delay)
    finally:
        await client.disconnect()

    logger.info(
        "telegram fetch done channel=%s new_saved=%d skipped=%d",
        channel,
        loaded,
        skipped,
    )
    return loaded


def fetch_telegram_source(
    source_uuid: str,
    cfg: dict[str, Any],
    source_name: str,
    max_new: int,
) -> int:
    channel = resolve_channel_username(cfg, source_name)
    if not channel:
        logger.error(
            "Не удалось определить username канала для источника %r: "
            "задайте в config JSON поле channel_username",
            source_name,
        )
        return 0
    return asyncio.run(_fetch_telegram_async(source_uuid, channel, max_new))
