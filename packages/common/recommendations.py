from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    skill_gap_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    skill_name: str
    importance_score: float
    recommended_course_titles: list[str] = Field(default_factory=list)


class VacancyRecommendation(BaseModel):
    recommendation_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    vacancy_id: UUID
    score: float
    phase: str = "phase_1"
    reasons: list[str] = Field(default_factory=list)


class ModelMetrics(BaseModel):
    precision: float | None = None
    recall: float | None = None
    ndcg: float | None = None
    mae: float | None = None
    rmse: float | None = None
