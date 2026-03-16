from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TelegramLinkRequest(BaseModel):
    telegram_id: str
    telegram_username: str | None = None


class TelegramLoginRequest(BaseModel):
    """Вход по Telegram: если пользователь уже привязан — логин, иначе создаётся новый аккаунт."""
    telegram_id: str
    telegram_username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str | None
    roles: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
