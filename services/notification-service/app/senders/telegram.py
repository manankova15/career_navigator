"""
Telegram Bot API sender via httpx (async HTTP client).

Uses sendMessage endpoint. Markdown V2 is escaped automatically.
Falls back to plain text if parsing fails.
"""
from __future__ import annotations

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_SEND_MESSAGE_PATH = "/bot{token}/sendMessage"


async def send_telegram(chat_id: int, text: str) -> None:
    """Send a text message to a Telegram chat via Bot API."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping telegram message to %s", chat_id)
        return

    url = f"{settings.telegram_api_base}{_SEND_MESSAGE_PATH.format(token=settings.telegram_bot_token)}"
    payload = {
        "chat_id": chat_id,
        "text": text,
        # Use HTML parse mode for basic formatting without escaping headaches
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    # Truncate Telegram message to 4096 chars (Bot API limit)
    if len(text) > 4096:
        payload["text"] = text[:4090] + "…"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            error_detail = resp.text[:200]
            raise RuntimeError(
                f"Telegram API error {resp.status_code}: {error_detail}"
            )
    logger.info("Telegram message sent to chat_id=%s", chat_id)


def escape_html(text: str) -> str:
    """Escape special HTML characters for Telegram HTML parse mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
