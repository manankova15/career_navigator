from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: str = "v1"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str
    payload: dict
