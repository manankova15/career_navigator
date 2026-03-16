from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

Channel = Literal["email", "telegram", "in-app"]
NotificationStatus = Literal["pending", "sent", "failed", "read", "skipped"]
DeliveryStatus = Literal["queued", "sending", "sent", "failed", "skipped"]


# ── Dispatch ──────────────────────────────────────────────────────────────────

class DispatchRequest(BaseModel):
    """Payload to create and dispatch a notification."""
    user_id: UUID
    channel: Channel
    template_name: str
    context: dict[str, Any] = Field(default_factory=dict)
    # Optional: override the resolved email (e.g. provide it directly to avoid auth-service lookup)
    to_email: str | None = None


class BulkDispatchRequest(BaseModel):
    """Dispatch the same notification to multiple users."""
    user_ids: list[UUID] = Field(min_length=1, max_length=500)
    channel: Channel
    template_name: str
    context: dict[str, Any] = Field(default_factory=dict)


# ── Notification out ──────────────────────────────────────────────────────────

class DeliveryOut(BaseModel):
    id: UUID
    channel: Channel
    status: DeliveryStatus
    attempt_count: int
    last_error: str | None
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    channel: Channel
    template_name: str
    subject: str | None
    body: str
    status: NotificationStatus
    read_at: datetime | None
    created_at: datetime
    deliveries: list[DeliveryOut]

    model_config = {"from_attributes": True}


class NotificationSummaryOut(BaseModel):
    """Lightweight row for inbox listing."""
    id: UUID
    channel: Channel
    template_name: str
    subject: str | None
    status: NotificationStatus
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPage(BaseModel):
    items: list[NotificationSummaryOut]
    total: int
    unread_count: int
    page: int
    page_size: int


class DispatchResult(BaseModel):
    notification_id: UUID
    channel: Channel
    status: str
    message: str = "Notification queued for dispatch"


class BulkDispatchResult(BaseModel):
    queued: int
    notification_ids: list[UUID]


# ── Preferences ───────────────────────────────────────────────────────────────

class PreferencesUpsert(BaseModel):
    email_enabled: bool = True
    telegram_enabled: bool = False
    telegram_chat_id: int | None = None
    digest_enabled: bool = True
    digest_day_of_week: int = Field(default=1, ge=1, le=7)


class PreferencesOut(BaseModel):
    id: UUID
    user_id: UUID
    email_enabled: bool
    telegram_enabled: bool
    telegram_chat_id: int | None
    digest_enabled: bool
    digest_day_of_week: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Admin stats ───────────────────────────────────────────────────────────────

class DeliveryStats(BaseModel):
    total_notifications: int
    sent: int
    failed: int
    pending: int
    success_rate_pct: float
