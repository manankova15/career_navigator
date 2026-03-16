from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ServiceEnvelope(BaseModel):
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any]


class Pagination(BaseModel):
    limit: int = 20
    offset: int = 0
