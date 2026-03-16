import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from .database import Base


class NotificationPreference(Base):
    """Per-user channel preferences and Telegram chat binding."""

    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    email_enabled = Column(Boolean, nullable=False, server_default="true")
    telegram_enabled = Column(Boolean, nullable=False, server_default="false")
    # Telegram chat_id is stored once the user links their account
    telegram_chat_id = Column(BigInteger, nullable=True)
    digest_enabled = Column(Boolean, nullable=False, server_default="true")
    # ISO weekday: 1=Monday … 7=Sunday
    digest_day_of_week = Column(Integer, nullable=False, server_default="1")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Notification(Base):
    """A rendered notification record for one user."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # email | telegram | in-app
    channel = Column(String(20), nullable=False)
    template_name = Column(String(100), nullable=False)
    subject = Column(String(300), nullable=True)
    body = Column(Text, nullable=False)
    # Original context used to render the template
    context = Column(JSONB, nullable=False, server_default="{}")
    # pending | sent | failed | read
    status = Column(String(20), nullable=False, server_default="pending")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deliveries = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Speed up per-user inbox queries
        # (user_id, created_at DESC)
    )


class NotificationDelivery(Base):
    """Tracks each actual dispatch attempt for a notification."""

    __tablename__ = "notification_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(20), nullable=False)
    # queued | sending | sent | failed
    status = Column(String(20), nullable=False, server_default="queued")
    attempt_count = Column(Integer, nullable=False, server_default="0")
    last_error = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    notification = relationship("Notification", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("notification_id", name="uq_delivery_notification"),
    )
