"""
Альтернативный (web-preview) загрузчик публичных Telegram-каналов.

Не требует Telethon-сессии: использует страницу https://t.me/s/<channel>,
которую Telegram отдаёт без авторизации для любого публичного канала.

Используется как fallback, если ``.tg_session`` отсутствует или Telethon
сессия не авторизована — тогда админ-панель не блокируется и автодозагрузка
работает «из коробки» только при наличии публичности у канала.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from ..config import settings
from ..internal_jwt import make_admin_access_token
from ..telegram_parse import parse_message

logger = logging.getLogger(__name__)


_PAGE_MESSAGE_RE = re.compile(
    r'<div class="tgme_widget_message[^"]*"\s+data-post="([^"]+)"',
    re.IGNORECASE,
)
_TEXT_BLOCK_RE = re.compile(
    r'<div class="tgme_widget_message_text[^"]*"\s*[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
_DATETIME_RE = re.compile(
    r'<time[^>]+datetime="([^"]+)"',
    re.IGNORECASE,
)
_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_BEFORE_RE = re.compile(
    r'<a[^>]+class="[^"]*tme_messages_more[^"]*"[^>]+data-before="(\d+)"',
    re.IGNORECASE,
)


_HTML_ENTITIES = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&nbsp;": " ",
}


def _unescape(text: str) -> str:
    for k, v in _HTML_ENTITIES.items():
        text = text.replace(k, v)
    # числовые сущности вида &#1234;
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    return text


def _html_to_text(html: str) -> str:
    html = _BR_RE.sub("\n", html)
    text = _TAG_RE.sub("", html)
    return _unescape(text).strip()


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
    except Exception as exc:  # noqa: BLE001
        logger.error("vacancy canonical POST error: %s", exc)
        return False


def _fetch_page(channel: str, before: int | None) -> str | None:
    url = f"https://t.me/s/{channel}"
    params = {}
    if before:
        params["before"] = str(before)
    try:
        with httpx.Client(
            timeout=20.0,
            headers={
                "User-Agent": settings.hh_user_agent,
                "Accept-Language": "ru,en;q=0.8",
            },
            follow_redirects=True,
        ) as client:
            resp = client.get(url, params=params or None)
        if resp.status_code != 200:
            logger.warning(
                "t.me/s/%s preview status=%s (channel может быть приватным)",
                channel,
                resp.status_code,
            )
            return None
        return resp.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("t.me/s/%s fetch error: %s", channel, exc)
        return None


def _parse_page(html: str) -> tuple[list[dict[str, Any]], int | None]:
    """Возвращает (messages, next_before).

    next_before — параметр для подгрузки более старых сообщений.
    """
    messages: list[dict[str, Any]] = []

    # Грубо разбиваем страницу по началу message-блоков.
    starts = [m.start() for m in _PAGE_MESSAGE_RE.finditer(html)]
    starts.append(len(html))
    for i, idx in enumerate(starts[:-1]):
        chunk = html[idx : starts[i + 1]]
        post_match = _PAGE_MESSAGE_RE.search(chunk)
        if not post_match:
            continue
        data_post = post_match.group(1)  # вид "channel/123"
        try:
            msg_id_str = data_post.split("/")[-1]
            msg_id = int(msg_id_str)
        except (ValueError, IndexError):
            continue

        text_match = _TEXT_BLOCK_RE.search(chunk)
        text = _html_to_text(text_match.group(1)) if text_match else ""

        dt_match = _DATETIME_RE.search(chunk)
        if dt_match:
            try:
                # формат вида 2024-12-31T18:30:00+00:00
                dt = datetime.fromisoformat(dt_match.group(1))
            except ValueError:
                dt = datetime.now(tz=timezone.utc)
        else:
            dt = datetime.now(tz=timezone.utc)

        messages.append({"id": msg_id, "text": text, "date": dt})

    # Параметр пагинации (для подгрузки более старых).
    before_match = _BEFORE_RE.search(html)
    next_before = int(before_match.group(1)) if before_match else None

    # Telegram отдаёт сообщения от старых к новым; перевернём, чтобы новые шли первыми.
    messages.sort(key=lambda x: x["id"], reverse=True)
    return messages, next_before


def fetch_public_channel_web(
    source_uuid: str,
    channel: str,
    max_new: int,
) -> int:
    """Скачать сообщения из публичного канала через web-preview (t.me/s/...).

    Возвращает число сохранённых canonical-вакансий.
    Если канал не публичный, возвращает 0 (предупреждение в логе).
    """
    loaded = 0
    skipped = 0
    seen_ids: set[int] = set()
    before: int | None = None
    pages = 0
    max_pages = max(1, (max_new // 20) + 2)

    while loaded < max_new and pages < max_pages:
        html = _fetch_page(channel, before)
        if not html:
            break
        msgs, next_before = _parse_page(html)
        pages += 1
        if not msgs:
            break

        for msg in msgs:
            if msg["id"] in seen_ids:
                continue
            seen_ids.add(msg["id"])
            text = msg["text"]
            if not text:
                skipped += 1
                continue
            vacancy = parse_message(
                msg["id"], text, msg["date"], channel, source_uuid
            )
            if vacancy is None:
                skipped += 1
                continue
            if _post_canonical(vacancy):
                loaded += 1
                logger.info(
                    "tg-web channel=%s loaded=%d/%d external=%s",
                    channel,
                    loaded,
                    max_new,
                    vacancy.get("external_id"),
                )
            else:
                skipped += 1

            if loaded >= max_new:
                break

        if loaded >= max_new:
            break
        if not next_before or next_before in (0,):
            break
        before = next_before

    logger.info(
        "tg-web fetch done channel=%s loaded=%d skipped=%d pages=%d",
        channel,
        loaded,
        skipped,
        pages,
    )
    return loaded
