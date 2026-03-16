import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .database import Base


class UserEvent(Base):
    """Lightweight event stream: key user actions sent by other services."""
    __tablename__ = "analytics_user_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    # vacancy_viewed | recommendation_clicked | assessment_completed |
    # vacancy_saved | assessment_started | login
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    properties = Column(JSONB, nullable=False, server_default="{}")
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AssessmentStat(Base):
    """Aggregated stats per user × assessment."""
    __tablename__ = "analytics_assessment_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(UUID(as_uuid=True), nullable=False)
    topic = Column(String(100), nullable=True)
    attempts_count = Column(Integer, nullable=False, server_default="0")
    best_percentage = Column(Float, nullable=False, server_default="0")
    last_percentage = Column(Float, nullable=False, server_default="0")
    avg_percentage = Column(Float, nullable=False, server_default="0")
    last_attempted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "assessment_id", name="uq_astat_user_assessment"),
    )


class DailyActiveUsers(Base):
    """Daily aggregation: distinct users who logged any event."""
    __tablename__ = "analytics_daily_active_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(String(10), nullable=False, unique=True)  # YYYY-MM-DD
    user_count = Column(Integer, nullable=False, server_default="0")
    event_count = Column(Integer, nullable=False, server_default="0")
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
