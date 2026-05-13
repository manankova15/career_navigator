import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .database import Base


class VacancySource(Base):
    __tablename__ = "vacancy_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)   # api | html | telegram
    base_url = Column(String(500), nullable=True)
    schedule = Column(String(100), nullable=False, server_default="0 */2 * * *")
    ttl_hours = Column(Integer, nullable=False, server_default="24")
    enabled = Column(Boolean, nullable=False, server_default="true")
    # source-specific: api_key, headers, query_params, area_id, etc.
    config = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IngestionRun(Base):
    """История запусков fetch_source — пишется воркером ingestion-worker."""

    __tablename__ = "ingestion_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_name = Column(String(200), nullable=True)
    source_type = Column(String(50), nullable=True)
    task_id = Column(String(80), nullable=True, index=True)
    # running | success | failed | skipped
    status = Column(String(20), nullable=False, server_default="running")
    new_vacancies = Column(Integer, nullable=False, server_default="0")
    max_vacancies = Column(Integer, nullable=True)
    reason = Column(String(200), nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)


class SystemSetting(Base):
    """Глобальные настройки (расписание ingestion и т.п.)."""

    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False, server_default="{}")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
