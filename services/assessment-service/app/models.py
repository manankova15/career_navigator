import uuid
from datetime import datetime

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class Assessment(Base):
    """A named set of tasks/questions on a specific topic."""

    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, server_default="medium")
    related_skills = Column(JSONB, nullable=False, server_default="[]")
    is_published = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items = relationship(
        "AssessmentItem",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentItem.position",
    )
    attempts = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class AssessmentItem(Base):
    """A single question or task within an assessment."""

    __tablename__ = "assessment_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position = Column(Integer, nullable=False, server_default="0")
    prompt = Column(Text, nullable=False)
    # quiz | multi_select | short_text | case
    mode = Column(String(20), nullable=False)
    # [{id: str, text: str}] – choices for quiz / multi-select
    options = Column(JSONB, nullable=False, server_default="[]")
    # list of option ids that are correct (quiz: one, multi-select: many)
    correct_option_ids = Column(JSONB, nullable=False, server_default="[]")
    # keywords expected in free-text answers
    expected_keywords = Column(JSONB, nullable=False, server_default="[]")
    # [{criterion: str, weight: float}] – rubric for case / short-text
    rubric_checklist = Column(JSONB, nullable=False, server_default="[]")
    max_score = Column(Float, nullable=False, server_default="1.0")
    related_skills = Column(JSONB, nullable=False, server_default="[]")
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="items")
    answers = relationship(
        "AssessmentAnswer",
        back_populates="item",
        cascade="all, delete-orphan",
    )


class AssessmentAttempt(Base):
    """One user's single run through an assessment."""

    __tablename__ = "assessment_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # completed | in_progress | abandoned
    status = Column(String(20), nullable=False, server_default="completed")
    # For in_progress: [{item_id, selected_option_ids, text_answer}]
    progress_answers = Column(JSONB, nullable=False, server_default="[]")
    earned_score = Column(Float, nullable=False, server_default="0")
    max_score = Column(Float, nullable=False, server_default="0")
    # 0-100 percentage
    percentage = Column(Float, nullable=False, server_default="0")
    weak_skills = Column(JSONB, nullable=False, server_default="[]")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="attempts")
    answers = relationship(
        "AssessmentAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AssessmentAnswer.created_at",
    )
    feedback = relationship(
        "AssessmentFeedback",
        back_populates="attempt",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AssessmentAnswer(Base):
    """User's answer to a single item within an attempt."""

    __tablename__ = "assessment_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    mode = Column(String(20), nullable=False)
    selected_option_ids = Column(JSONB, nullable=False, server_default="[]")
    text_answer = Column(Text, nullable=True)
    # null for subjective tasks (short-text, case)
    is_correct = Column(Boolean, nullable=True)
    earned_score = Column(Float, nullable=False, server_default="0")
    auto_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    item = relationship("AssessmentItem", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("attempt_id", "item_id", name="uq_answer_attempt_item"),
    )


class AssessmentFeedback(Base):
    """Aggregated feedback for a completed attempt."""

    __tablename__ = "assessment_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary = Column(Text, nullable=False)
    rubric_notes = Column(JSONB, nullable=False, server_default="[]")
    recommended_materials = Column(JSONB, nullable=False, server_default="[]")
    weak_skills = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="feedback")
