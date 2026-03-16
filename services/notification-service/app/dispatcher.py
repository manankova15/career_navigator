"""
Notification dispatcher.

Orchestrates: render template → look up channel credentials
→ call the appropriate sender → update delivery record.

Designed to be called from a FastAPI BackgroundTask so the HTTP
response is returned immediately and dispatch happens asynchronously.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from .config import settings
from .models import Notification, NotificationDelivery, NotificationPreference
from .senders.email import send_email
from .senders.telegram import send_telegram
from .templates import render

logger = logging.getLogger(__name__)


async def dispatch_notification(
    db: Session,
    notification_id: UUID,
    user_email: str | None = None,
) -> None:
    """
    Main dispatch coroutine.

    Steps:
      1. Load Notification + Delivery from DB.
      2. Check user preferences for channel opt-in.
      3. Send via the appropriate channel.
      4. Update delivery status (sent / failed).
      5. Update notification status.
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        logger.error("Notification %s not found in dispatch", notification_id)
        return

    delivery = (
        db.query(NotificationDelivery)
        .filter(NotificationDelivery.notification_id == notification_id)
        .first()
    )
    if not delivery:
        logger.error("Delivery record missing for notification %s", notification_id)
        return

    if delivery.attempt_count >= settings.max_delivery_attempts:
        logger.warning(
            "Max attempts reached for notification %s, skipping", notification_id
        )
        return

    delivery.status = "sending"
    delivery.attempt_count += 1
    db.commit()

    channel = notification.channel

    try:
        if channel == "email":
            if not user_email:
                raise ValueError("user_email required for email channel but not provided")
            await send_email(
                to_address=user_email,
                subject=notification.subject or "(no subject)",
                body=notification.body,
                html_body=_get_html_body(notification),
            )

        elif channel == "telegram":
            prefs = _get_prefs(db, notification.user_id)
            if prefs is None or not prefs.telegram_chat_id:
                raise ValueError(
                    f"No Telegram chat_id for user {notification.user_id}"
                )
            if prefs and not prefs.telegram_enabled:
                logger.info(
                    "Telegram disabled for user %s, skipping", notification.user_id
                )
                delivery.status = "skipped"
                db.commit()
                return
            await send_telegram(
                chat_id=prefs.telegram_chat_id,
                text=notification.body,
            )

        elif channel == "in-app":
            # In-app notifications are stored in the DB and surfaced via GET /notifications/me
            # No external dispatch needed
            pass

        else:
            raise ValueError(f"Unknown channel: {channel}")

        delivery.status = "sent"
        delivery.sent_at = datetime.utcnow()
        delivery.last_error = None
        notification.status = "sent"

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to dispatch notification %s via %s", notification_id, channel)
        delivery.status = "failed"
        delivery.last_error = str(exc)[:500]
        notification.status = "failed"

    db.commit()


def _get_prefs(db: Session, user_id: UUID) -> NotificationPreference | None:
    return (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )


def _get_html_body(notification: Notification) -> str:
    """Re-render HTML body from template; fall back to plain body wrapped in <pre>."""
    try:
        msg = render(notification.template_name, notification.context or {})
        return msg.html_body
    except Exception:
        return f"<pre>{notification.body}</pre>"
