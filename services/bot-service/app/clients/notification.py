"""Client for notification-service."""
from __future__ import annotations

from ..config import settings
from .base import get_json, post_internal


async def dispatch_notification(
    user_id: str,
    channel: str,
    template_name: str,
    context: dict,
    to_email: str | None = None,
) -> bool:
    """Dispatch a notification via the internal token."""
    body: dict = {
        "user_id": user_id,
        "channel": channel,
        "template_name": template_name,
        "context": context,
    }
    if to_email:
        body["to_email"] = to_email
    try:
        await post_internal(
            f"{settings.notification_service_url}/notifications/dispatch", body
        )
        return True
    except Exception:
        return False


async def link_telegram_chat(token: str, chat_id: int) -> bool:
    try:
        await get_json(
            f"{settings.notification_service_url}/notifications/preferences/me/link-telegram",
            token,
            params={"chat_id": chat_id},
        )
        return True
    except Exception:
        return False
