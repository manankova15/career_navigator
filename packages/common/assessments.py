from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


AssessmentMode = Literal["quiz", "multi-select", "short-text", "case"]


class AssessmentItem(BaseModel):
    item_id: UUID = Field(default_factory=uuid4)
    prompt: str
    mode: AssessmentMode
    expected_keywords: list[str] = Field(default_factory=list)
    related_skills: list[str] = Field(default_factory=list)


class AssessmentAttemptRecord(BaseModel):
    attempt_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    assessment_id: UUID
    mode: AssessmentMode
    score: float = 0.0
    weak_skills: list[str] = Field(default_factory=list)


class AssessmentFeedbackRecord(BaseModel):
    attempt_id: UUID
    summary: str
    rubric_notes: list[str] = Field(default_factory=list)
    recommended_materials: list[str] = Field(default_factory=list)
