from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MetricDefinition(BaseModel):
    metric_id: UUID = Field(default_factory=uuid4)
    name: str
    owner_service: str
    latency_budget_ms: int | None = None


class NotificationDelivery(BaseModel):
    delivery_id: UUID = Field(default_factory=uuid4)
    notification_id: UUID
    channel: Literal["email", "telegram"]
    status: Literal["queued", "sent", "failed"] = "queued"
