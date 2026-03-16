import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .database import Base


class VacancySource(Base):
    __tablename__ = "vacancy_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)   # api | html | telegram
    base_url = Column(String(500), nullable=True)
    schedule = Column(String(100), nullable=False, server_default="0 */2 * * *")
    ttl_hours = Column(Integer, nullable=False, server_default="24")
    enabled = Column(Boolean, nullable=False, server_default="true")
    # source-specific: api_key, headers, query_params, area_id, etc.
    config = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
