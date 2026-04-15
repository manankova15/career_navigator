from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class SourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    source_type: Literal["api", "html", "telegram"]
    base_url: str | None = Field(None, max_length=500)
    schedule: str = Field("0 */2 * * *", max_length=100)
    ttl_hours: int = Field(24, ge=1, le=720)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class SourceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    base_url: str | None
    schedule: str
    ttl_hours: int
    enabled: bool
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceToggle(BaseModel):
    enabled: bool


class SourceSyncIn(BaseModel):
    """Параметры ручной дозагрузки (передаётся в Celery)."""

    max_vacancies: int | None = Field(
        None,
        ge=1,
        le=5000,
        description="Сколько новых вакансий максимум собрать (HH: новые raw; TG: успешных POST canonical)",
    )
