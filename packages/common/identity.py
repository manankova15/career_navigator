from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class UserRole(str):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class UserIdentity(BaseModel):
    identity_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    provider: str
    provider_subject: str
    email: EmailStr | None = None
    is_verified: bool = False
    linked_at: datetime = Field(default_factory=datetime.utcnow)


class UserAccount(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    full_name: str
    primary_email: EmailStr
    roles: list[str] = Field(default_factory=lambda: [UserRole.USER])
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
