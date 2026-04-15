from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class EventIn(BaseModel):
    user_id: UUID
    event_type: str
    resource_type: str | None = None
    resource_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class EventFromUserIn(BaseModel):
    """Событие от текущего пользователя (user_id берётся из JWT)."""
    event_type: str
    resource_type: str | None = None
    resource_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class AssessmentEventIn(BaseModel):
    user_id: UUID
    assessment_id: UUID
    topic: str | None = None
    percentage: float


class AssessmentStatOut(BaseModel):
    assessment_id: UUID
    topic: str | None
    attempts_count: int
    best_percentage: float
    last_percentage: float
    avg_percentage: float
    last_attempted_at: datetime | None
    model_config = {"from_attributes": True}


class UserProgressOut(BaseModel):
    user_id: UUID
    total_attempts: int
    avg_score: float
    best_score: float
    assessments_taken: int
    vacancy_views: int
    recommendation_clicks: int
    recent_stats: list[AssessmentStatOut]


class ProductMetricsOut(BaseModel):
    total_events: int
    total_users_with_events: int
    assessments_completed: int
    vacancy_views: int
    recommendation_clicks: int
    last_dau: int
    last_dau_date: str | None


class DauPoint(BaseModel):
    date: str
    users: int
    events: int


class DashboardOut(BaseModel):
    metrics: ProductMetricsOut
    dau_series: list[DauPoint]
