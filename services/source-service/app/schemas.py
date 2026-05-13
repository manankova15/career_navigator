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


class SourceSyncOut(BaseModel):
    """Ответ на постановку задачи дозагрузки в очередь."""

    source_id: str
    status: Literal["queued"] = "queued"
    task_id: str
    max_vacancies: int | None = None


class SyncJobStatusOut(BaseModel):
    """Срез состояния фоновой задачи ingestion по task_id."""

    task_id: str
    state: str
    ready: bool = False
    result: dict[str, Any] | None = None
    error: str | None = None


class IngestionRunOut(BaseModel):
    """Строка истории ingestion-запусков."""

    id: UUID
    source_id: UUID | None
    source_name: str | None
    source_type: str | None
    task_id: str | None
    status: str
    new_vacancies: int
    max_vacancies: int | None
    reason: str | None
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class IngestionRunsPage(BaseModel):
    items: list[IngestionRunOut]
    total: int
    page: int
    page_size: int


class IngestionScheduleOut(BaseModel):
    """Глобальные параметры автоматической дозагрузки."""

    fetch_interval_hours: int = Field(2, ge=1, le=168)
    normalize_interval_minutes: int = Field(30, ge=5, le=1440)


class IngestionScheduleUpdate(BaseModel):
    fetch_interval_hours: int | None = Field(None, ge=1, le=168)
    normalize_interval_minutes: int | None = Field(None, ge=5, le=1440)
