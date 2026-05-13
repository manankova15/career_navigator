"""
ORM models mirroring vacancy-service tables.
The ingestion-worker does NOT own migrations for these tables —
they are managed by vacancy-service and source-service.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID

from .database import Base


class VacancySource(Base):
    __tablename__ = "vacancy_sources"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(100))
    source_type = Column(String(50))
    base_url = Column(String(500))
    schedule = Column(String(100))
    ttl_hours = Column(Integer)
    enabled = Column(Boolean)
    config = Column(JSONB)


class RawVacancy(Base):
    __tablename__ = "raw_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(300), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_raw_vacancies_source_external"),
    )


class CanonicalVacancy(Base):
    __tablename__ = "canonical_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(300))
    title = Column(String(300), nullable=False)
    company = Column(String(300), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    location = Column(String(200))
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    salary_currency = Column(String(10), server_default="RUB")
    # Рублёвый эквивалент (приведённый к месяцу) — используется для сортировки
    # и фильтрации по зарплате независимо от исходной валюты вакансии.
    salary_from_rub = Column(Integer)
    salary_to_rub = Column(Integer)
    seniority = Column(String(50))
    employment_type = Column(ARRAY(String(50)))
    work_format = Column(ARRAY(String(30)), nullable=False, server_default=text("'{}'"))
    schedule_type = Column(String(30))
    experience_level = Column(String(30))
    salary_gross_type = Column(String(20))
    salary_period = Column(String(20))
    profession_area = Column(String(40))
    specialization = Column(String(80))
    location_country = Column(String(120))
    location_city = Column(String(120))
    education_level = Column(String(30))
    english_level = Column(String(20))
    company_industry = Column(String(200))
    source_name = Column(String(50))
    description = Column(Text)
    skills = Column(ARRAY(String(100)), server_default="{}")
    status = Column(String(50), server_default="active")
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_canonical_source_external"),
    )


class DeduplicationLog(Base):
    __tablename__ = "dedup_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_vacancy_id = Column(
        UUID(as_uuid=True), ForeignKey("canonical_vacancies.id", ondelete="CASCADE")
    )
    duplicate_vacancy_id = Column(
        UUID(as_uuid=True), ForeignKey("canonical_vacancies.id", ondelete="CASCADE")
    )
    similarity_score = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)


class IngestionRun(Base):
    """Постоянная история запусков fetch_source (миграция в source-service)."""

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
    """Глобальные настройки (расписание ingestion и т.п.) — миграция в source-service."""

    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False, server_default="{}")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
