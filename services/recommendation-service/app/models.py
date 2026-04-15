import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class RecommendationSession(Base):
    """One scoring run for one user."""
    __tablename__ = "recommendation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    algorithm = Column(String(50), nullable=False, server_default="content_v1")
    total_scored = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recommendations = relationship(
        "VacancyRecommendation",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="VacancyRecommendation.score.desc()",
    )
    skill_gaps = relationship(
        "SkillGapRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class VacancyRecommendation(Base):
    """Single recommended vacancy within a session."""
    __tablename__ = "vacancy_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=False)
    score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=False, server_default="0")
    location_score = Column(Float, nullable=False, server_default="0")
    salary_score = Column(Float, nullable=False, server_default="0")
    seniority_score = Column(Float, nullable=False, server_default="0")
    ml_score = Column(Float, nullable=True)
    matched_skills = Column(JSONB, nullable=False, server_default="[]")
    missing_skills = Column(JSONB, nullable=False, server_default="[]")
    reasons = Column(JSONB, nullable=False, server_default="[]")
    # User feedback: null | "positive" | "negative" | "saved"
    feedback = Column(String(20), nullable=True)
    feedback_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("RecommendationSession", back_populates="recommendations")

    __table_args__ = (
        UniqueConstraint("session_id", "vacancy_id", name="uq_rec_session_vacancy"),
    )


class SkillGapRecord(Base):
    """One missing skill in a skill-gap report for a session."""
    __tablename__ = "skill_gap_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)
    importance_score = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)
    recommended_resources = Column(JSONB, nullable=False, server_default="[]")
    rank = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("RecommendationSession", back_populates="skill_gaps")


class UserLikedVacancy(Base):
    """Server-side vacancy like for personalization (soft-unlike via unliked_at)."""
    __tablename__ = "user_liked_vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=False)
    liked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unliked_at = Column(DateTime, nullable=True)
    vacancy_title = Column(String(300), nullable=True)
    vacancy_skills = Column(JSONB, nullable=True, server_default="[]")

    __table_args__ = (UniqueConstraint("user_id", "vacancy_id", name="uq_user_liked_vacancy"),)
