from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ── Shared ────────────────────────────────────────────────────────────────────

AssessmentMode = Literal["quiz", "multi_select", "short_text", "case"]
Difficulty = Literal["easy", "medium", "hard"]


class OptionSchema(BaseModel):
    id: str
    text: str


class RubricCriterion(BaseModel):
    criterion: str
    weight: float = 1.0


# ── Assessment CRUD ───────────────────────────────────────────────────────────

class AssessmentItemCreate(BaseModel):
    position: int = 0
    prompt: str
    mode: AssessmentMode
    options: list[OptionSchema] = Field(default_factory=list)
    correct_option_ids: list[str] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    rubric_checklist: list[RubricCriterion] = Field(default_factory=list)
    max_score: float = Field(default=1.0, gt=0)
    related_skills: list[str] = Field(default_factory=list)
    explanation: str | None = None


class AssessmentItemOut(BaseModel):
    id: UUID
    assessment_id: UUID
    position: int
    prompt: str
    mode: AssessmentMode
    options: list[OptionSchema]
    max_score: float
    related_skills: list[str]
    explanation: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssessmentItemAdminOut(AssessmentItemOut):
    """Full item schema including answer keys – admin only."""
    correct_option_ids: list[str]
    expected_keywords: list[str]
    rubric_checklist: list[RubricCriterion]


class AssessmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    topic: str = Field(min_length=1, max_length=100)
    difficulty: Difficulty = "medium"
    related_skills: list[str] = Field(default_factory=list)
    is_published: bool = False
    items: list[AssessmentItemCreate] = Field(default_factory=list)


class AssessmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    topic: str | None = None
    difficulty: Difficulty | None = None
    related_skills: list[str] | None = None
    is_published: bool | None = None


class AssessmentOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    topic: str
    difficulty: str
    related_skills: list[str]
    is_published: bool
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssessmentWithItemsOut(AssessmentOut):
    """Assessment with items, hiding answer keys for regular users."""
    items: list[AssessmentItemOut]


class AssessmentWithItemsAdminOut(AssessmentOut):
    """Assessment with full item data for admin."""
    items: list[AssessmentItemAdminOut]


# ── Attempt submission ────────────────────────────────────────────────────────

class AnswerIn(BaseModel):
    item_id: UUID
    selected_option_ids: list[str] = Field(default_factory=list)
    text_answer: str | None = None


class AttemptSubmit(BaseModel):
    answers: list[AnswerIn] = Field(min_length=1)
    attempt_id: UUID | None = None


class ProgressSaveIn(BaseModel):
    """Partial answers for in-progress attempt (to resume later)."""
    answers: list[AnswerIn] = Field(default_factory=list)


# ── Attempt output ────────────────────────────────────────────────────────────

class AnswerOut(BaseModel):
    id: UUID
    item_id: UUID
    mode: AssessmentMode
    selected_option_ids: list[str]
    text_answer: str | None
    is_correct: bool | None
    earned_score: float
    auto_feedback: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttemptOut(BaseModel):
    id: UUID
    user_id: UUID
    assessment_id: UUID
    status: str
    earned_score: float
    max_score: float
    percentage: float
    passed: bool = False
    weak_skills: list[str]
    completed_at: datetime | None
    created_at: datetime
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    answers: list[AnswerOut]
    progress_answers: list[dict] = Field(default_factory=list, description="For in_progress: saved answers to restore")

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_passed(cls, attempt, pass_threshold: float = 60.0):
        obj = cls.model_validate(attempt)
        obj.passed = attempt.percentage >= pass_threshold
        obj.started_at = attempt.created_at
        obj.submitted_at = attempt.completed_at
        if getattr(attempt, "progress_answers", None) is not None:
            obj.progress_answers = attempt.progress_answers or []
        return obj


class AttemptSummaryOut(BaseModel):
    """Lightweight attempt row for history listings."""
    id: UUID
    assessment_id: UUID
    assessment_title: str | None = None
    status: str
    earned_score: float
    max_score: float
    percentage: float
    passed: bool = False
    weak_skills: list[str]
    completed_at: datetime | None
    created_at: datetime
    started_at: datetime | None = None
    submitted_at: datetime | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_passed(cls, attempt, pass_threshold: float = 60.0, assessment_title: str | None = None):
        obj = cls.model_validate(attempt)
        obj.passed = attempt.percentage >= pass_threshold
        obj.started_at = attempt.created_at
        obj.submitted_at = attempt.completed_at
        if assessment_title is not None:
            obj.assessment_title = assessment_title
        elif getattr(attempt, "assessment", None) is not None:
            obj.assessment_title = attempt.assessment.title
        return obj


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackOut(BaseModel):
    id: UUID
    attempt_id: UUID
    summary: str
    rubric_notes: list[str]
    recommended_materials: list[str]
    weak_skills: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination wrapper ────────────────────────────────────────────────────────

class AssessmentPage(BaseModel):
    items: list[AssessmentOut]
    total: int
    page: int
    page_size: int


class AdminAssessmentStatsOut(BaseModel):
    completed_attempts: int
    users_with_completed_attempts: int


class AttemptPage(BaseModel):
    items: list[AttemptSummaryOut]
    total: int
    page: int
    page_size: int
