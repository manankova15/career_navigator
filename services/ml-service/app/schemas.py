"""
Input/output contracts for the ML service.
All data arrives via HTTP — the service is stateless (no DB, no external models).

Algorithm version: ``hybrid_ahp_v3`` — see
``docs/recommendation_model_v3.md`` for the full mathematical specification.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Inputs ────────────────────────────────────────────────────────────────────

class UserProfileInput(BaseModel):
    user_id: UUID
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_formats: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    target_industry: str | None = None
    # Категории/спеки с profile-service (выпадающие списки), не из текстового classifier
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_specializations: list[str] = Field(default_factory=list)
    # Из лайков для reasons; скоринг — через BehaviorInput
    liked_skills_top: list[str] = Field(default_factory=list)
    liked_titles: list[str] = Field(default_factory=list)
    total_likes: int = 0


class VacancyInput(BaseModel):
    vacancy_id: UUID
    title: str
    company: str
    location: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    # Канонические profession_area / specialization (модель v3 §3)
    profession_area: str | None = None
    specialization: str | None = None
    work_format: list[str] = Field(default_factory=list)


class BehaviorInput(BaseModel):
    """Агрегат сигналов из recommendation-service (§4 v3), без доп. сглаживания в ml-service"""

    total_signals: int = 0
    category_pref: dict[str, float] = Field(default_factory=dict)
    specialization_pref: dict[str, float] = Field(default_factory=dict)
    skill_pref: dict[str, float] = Field(default_factory=dict)
    title_token_pref: dict[str, float] = Field(default_factory=dict)
    positive_vacancy_ids: list[str] = Field(default_factory=list)
    negative_vacancy_ids: list[str] = Field(default_factory=list)


class ScoreRequest(BaseModel):
    profile: UserProfileInput
    vacancies: list[VacancyInput]
    behavior: BehaviorInput = Field(default_factory=BehaviorInput)


class SkillGapRequest(BaseModel):
    profile: UserProfileInput
    target_vacancies: list[VacancyInput]


# ── Outputs ───────────────────────────────────────────────────────────────────

class ScoredVacancy(BaseModel):
    vacancy_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    base_score: float = Field(default=0.0, ge=0.0, le=1.0)
    behavior_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tau: float = Field(default=0.0, ge=0.0, le=1.0)
    multiplier: float = 1.0
    direct_signal: float | None = None
    skill_score: float
    location_score: float
    salary_score: float
    seniority_score: float
    format_score: float = 0.0
    category_score: float = 0.5
    specialization_score: float = 0.5
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
    features: dict[str, Any] = Field(default_factory=dict)


class ScoreResponse(BaseModel):
    user_id: UUID
    algorithm: str = "hybrid_ahp_v3"
    total_scored: int
    results: list[ScoredVacancy]


class SkillGapItem(BaseModel):
    skill_name: str
    importance_score: float = Field(ge=0.0, le=1.0)
    frequency: int
    recommended_resources: list[str] = Field(default_factory=list)


class SkillGapResponse(BaseModel):
    user_id: UUID
    total_target_vacancies: int
    gaps: list[SkillGapItem]
