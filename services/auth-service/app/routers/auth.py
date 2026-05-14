import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import (
    create_refresh_token,
    create_user,
    get_identity_by_email,
    get_or_create_user_by_telegram,
    get_refresh_token,
    get_user_by_id,
    get_user_primary_email,
    get_user_roles,
    link_telegram,
    reset_password_for_email,
    revoke_refresh_token,
)
from ..database import get_db
from ..deps import get_current_user
from ..email_sender import build_password_reset_email, send_email
from ..models import User
from ..schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TelegramLinkRequest,
    TelegramLoginRequest,
    TokenResponse,
    UserOut,
)
from ..security import create_access_token, verify_password

logger = logging.getLogger(__name__)


def _generate_temp_password(length: int = 12) -> str:
    """Generate a random URL-safe temporary password with letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(db: Session, user: User) -> TokenResponse:
    roles = get_user_roles(db, user.id)
    return TokenResponse(
        access_token=create_access_token(str(user.id), roles),
        refresh_token=create_refresh_token(db, user.id),
    )


def _user_out(db: Session, user: User) -> UserOut:
    return UserOut(
        user_id=user.id,
        full_name=user.full_name,
        email=get_user_primary_email(db, user.id),
        roles=get_user_roles(db, user.id),
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if get_identity_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = create_user(db, payload.full_name, payload.email, payload.password)
    return _token_response(db, user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identity = get_identity_by_email(db, payload.email)
    if not identity or not identity.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not verify_password(payload.password, identity.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    user = get_user_by_id(db, identity.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )
    return _token_response(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_obj = get_refresh_token(db, payload.refresh_token)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    revoke_refresh_token(db, payload.refresh_token)
    user = get_user_by_id(db, token_obj.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )
    return _token_response(db, user)


@router.post("/logout")
async def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, payload.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _user_out(db, current_user)


@router.post("/telegram-login", response_model=TokenResponse)
async def telegram_login(
    payload: TelegramLoginRequest, db: Session = Depends(get_db)
):
    """Вход по Telegram: по telegram_id выдаётся JWT; если пользователя нет — создаётся новый."""
    user = get_or_create_user_by_telegram(
        db,
        payload.telegram_id,
        payload.telegram_username,
        payload.first_name,
        payload.last_name,
    )
    return _token_response(db, user)


@router.post("/link-telegram")
async def link_telegram_account(
    payload: TelegramLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_telegram(db, current_user.id, payload.telegram_id, payload.telegram_username)
    return {"message": "Telegram linked", "telegram_id": payload.telegram_id}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    """Generate a temporary password and email it to the user.

    For privacy we return the same message regardless of whether the email
    exists in the system, so this endpoint cannot be used for enumeration.
    """
    generic_response = ForgotPasswordResponse(
        message=(
            "Если такой email зарегистрирован в системе, мы отправили "
            "на него письмо с временным паролем."
        )
    )

    identity = get_identity_by_email(db, payload.email)
    if not identity:
        return generic_response

    user = get_user_by_id(db, identity.user_id)
    if not user or not user.is_active:
        return generic_response

    new_password = _generate_temp_password()
    if not reset_password_for_email(db, payload.email, new_password):
        return generic_response

    subject, plain, html = build_password_reset_email(user.full_name, new_password)
    ok = await send_email(payload.email, subject, plain, html)
    if not ok:
        logger.warning(
            "Password reset email could not be sent to %s — password was rotated anyway",
            payload.email,
        )
    return generic_response
