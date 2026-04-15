from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationOut(BaseModel):
    id: UUID
    vacancy_id: UUID
    score: float
    ml_score: float | None = None
    skill_score: float
    location_score: float
    salary_score: float
    seniority_score: float
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
    """Paginated feed of latest recommendations for the user."""
    items: list[RecommendationOut]
    session_id: UUID
    session_created_at: datetime
    total: int
    algorithm: str


class VacancyLikeIn(BaseModel):
    vacancy_title: str | None = None
    vacancy_skills: list[str] = Field(default_factory=list)


class LikedVacancyOut(BaseModel):
    id: UUID
    vacancy_id: UUID
    vacancy_title: str | None
    vacancy_skills: list[str]
    liked_at: datetime

    model_config = {"from_attributes": True}
