"""
CRUD operations for notification-service.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Notification, NotificationDelivery, NotificationPreference
from .schemas import PreferencesUpsert
from .templates import render


# ── Preferences ───────────────────────────────────────────────────────────────

def get_preferences(db: Session, user_id: UUID) -> NotificationPreference | None:
    return (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )


def upsert_preferences(
    db: Session, user_id: UUID, payload: PreferencesUpsert
) -> NotificationPreference:
    prefs = get_preferences(db, user_id)
    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)

    prefs.email_enabled = payload.email_enabled
    prefs.telegram_enabled = payload.telegram_enabled
    if payload.telegram_chat_id is not None:
        prefs.telegram_chat_id = payload.telegram_chat_id
    prefs.digest_enabled = payload.digest_enabled
    prefs.digest_day_of_week = payload.digest_day_of_week
    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


def set_telegram_chat_id(db: Session, user_id: UUID, chat_id: int) -> NotificationPreference:
    """Called from bot-service deep-link flow to bind chat_id."""
    prefs = get_preferences(db, user_id)
    if prefs is None:
        prefs = NotificationPreference(
            user_id=user_id,
            telegram_chat_id=chat_id,
            telegram_enabled=True,
        )
        db.add(prefs)
    else:
        prefs.telegram_chat_id = chat_id
        prefs.telegram_enabled = True
        prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


# ── Notifications ─────────────────────────────────────────────────────────────

def create_notification(
    db: Session,
    user_id: UUID,
    channel: str,
    template_name: str,
    context: dict,
) -> Notification:
    """Render the template and persist notification + delivery records."""
    msg = render(template_name, context)

    notification = Notification(
        user_id=user_id,
        channel=channel,
        template_name=template_name,
        subject=msg.subject,
        body=msg.body,
        context=context,
        status="pending",
    )
    db.add(notification)
    db.flush()

    delivery = NotificationDelivery(
        notification_id=notification.id,
        channel=channel,
        status="queued",
    )
    db.add(delivery)
    db.commit()
    db.refresh(notification)
    return notification


def get_notification(db: Session, notification_id: UUID) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def list_user_notifications(
    db: Session,
    user_id: UUID,
    *,
    unread_only: bool = False,
    channel: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Notification], int, int]:
    """Returns (items, total_count, unread_count)."""
    base_q = db.query(Notification).filter(Notification.user_id == user_id)
    if channel:
        base_q = base_q.filter(Notification.channel == channel)

    unread_count = base_q.filter(Notification.status != "read").count()

    if unread_only:
        base_q = base_q.filter(Notification.status != "read")

    total = base_q.count()
    items = (
        base_q.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total, unread_count


def mark_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification | None:
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )
    if not notif:
        return None
    if notif.status != "read":
        notif.status = "read"
        notif.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, user_id: UUID) -> int:
    """Mark all unread notifications as read. Returns number of updated rows."""
    now = datetime.utcnow()
    updated = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.status != "read",
        )
        .all()
    )
    count = len(updated)
    for n in updated:
        n.status = "read"
        n.read_at = now
    db.commit()
    return count


# ── Admin stats ───────────────────────────────────────────────────────────────

def get_delivery_stats(db: Session) -> dict:
    total = db.query(func.count(Notification.id)).scalar() or 0
    sent = (
        db.query(func.count(Notification.id))
        .filter(Notification.status == "sent")
        .scalar()
        or 0
    )
    failed = (
        db.query(func.count(Notification.id))
        .filter(Notification.status == "failed")
        .scalar()
        or 0
    )
    pending = (
        db.query(func.count(Notification.id))
        .filter(Notification.status == "pending")
        .scalar()
        or 0
    )
    success_rate = round(sent / total * 100, 2) if total > 0 else 0.0
    return {
        "total_notifications": total,
        "sent": sent,
        "failed": failed,
        "pending": pending,
        "success_rate_pct": success_rate,
    }


def retry_failed(db: Session, notification_id: UUID) -> NotificationDelivery | None:
    """Reset a failed delivery back to 'queued' so it can be retried."""
    delivery = (
        db.query(NotificationDelivery)
        .filter(NotificationDelivery.notification_id == notification_id)
        .first()
    )
    if not delivery or delivery.status != "failed":
        return None
    delivery.status = "queued"
    delivery.last_error = None

    notif = get_notification(db, notification_id)
    if notif:
        notif.status = "pending"

    db.commit()
    db.refresh(delivery)
    return delivery
