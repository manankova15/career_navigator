from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationOut(BaseModel):
    id: UUID
    vacancy_id: UUID
    score: float
    base_score: float = 0.0
    personal_boost: float = 0.0
    direct_signal: float | None = None
    ml_score: float | None = None
    category_score: float = 0.5
    specialization_score: float = 0.5
    skill_score: float
    role_score: float = 0.0
    location_score: float
    salary_score: float
    seniority_score: float
    format_score: float = 0.0
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
    feedback: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: UUID
    user_id: UUID
    algorithm: str
    total_scored: int
    created_at: datetime
    recommendations: list[RecommendationOut]

    model_config = {"from_attributes": True}


class SkillGapOut(BaseModel):
    skill_name: str
    importance_score: float
    frequency: int
    rank: int
    recommended_resources: list[str]

    model_config = {"from_attributes": True}


class SkillGapReportOut(BaseModel):
    session_id: UUID
    user_id: UUID
    algorithm: str
    total_target_vacancies: int
    gaps: list[SkillGapOut]


class FeedbackIn(BaseModel):
    feedback: Literal["positive", "negative", "saved"]


class RecommendFeedPage(BaseModel):
    items: list[RecommendationOut]
    session_id: UUID
    session_created_at: datetime
    total: int
    algorithm: str


class VacancyLikeIn(BaseModel):
    vacancy_title: str | None = None
    vacancy_skills: list[str] = Field(default_factory=list)
    vacancy_category: str | None = None
    vacancy_specialization: str | None = None


class LikedVacancyOut(BaseModel):
    id: UUID
    vacancy_id: UUID
    vacancy_title: str | None
    vacancy_skills: list[str]
    vacancy_category: str | None = None
    vacancy_specialization: str | None = None
    liked_at: datetime

    model_config = {"from_attributes": True}


class InteractionIn(BaseModel):
    """Explicit interest signal from the vacancy detail page or bot buttons."""
    sentiment: Literal["positive", "negative", "neutral"]
    source: str | None = None
    vacancy_title: str | None = None
    vacancy_skills: list[str] = Field(default_factory=list)
    vacancy_category: str | None = None
    vacancy_specialization: str | None = None


class InteractionOut(BaseModel):
    id: UUID
    vacancy_id: UUID
    sentiment: float
    kind: str
    updated_at: datetime

    model_config = {"from_attributes": True}
