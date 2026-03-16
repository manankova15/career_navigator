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
    currency = Column(String(10), server_default="RUB")
    seniority = Column(String(50))
    employment_type = Column(String(50))
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
