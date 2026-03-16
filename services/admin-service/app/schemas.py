from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: UUID
    actor_user_id: UUID
    actor_email: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


class SyncTriggerResult(BaseModel):
    source_id: str
    status: str
    message: str


class AdminActionResult(BaseModel):
    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class VacancyModerate(BaseModel):
    status: str  # active | archived | blocked


class AssessmentPublish(BaseModel):
    is_published: bool


class UserStatusUpdate(BaseModel):
    is_active: bool
