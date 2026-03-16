import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID

from .database import Base


class RawVacancy(Base):
    __tablename__ = "raw_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(300), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_raw_vacancies_source_external"),
    )


class CanonicalVacancy(Base):
    __tablename__ = "canonical_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(300), nullable=True)
    title = Column(String(300), nullable=False)
    company = Column(String(300), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    location = Column(String(200), nullable=True)
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=True, server_default="RUB")
    seniority = Column(String(50), nullable=True)
    employment_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    skills = Column(ARRAY(String(100)), nullable=False, server_default="{}")
    # active | expired | archived | blocked
    status = Column(String(50), nullable=False, server_default="active")
    published_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    # Managed by DB trigger — do not set manually
    search_vector = Column(TSVECTOR, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_canonical_source_external"),
        Index("ix_canonical_vacancies_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_canonical_vacancies_status", "status"),
        Index("ix_canonical_vacancies_location", "location"),
        Index("ix_canonical_vacancies_seniority", "seniority"),
    )


class DeduplicationLog(Base):
    __tablename__ = "dedup_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_vacancy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("canonical_vacancies.id", ondelete="CASCADE"),
        nullable=False,
    )
    duplicate_vacancy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("canonical_vacancies.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity_score = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
