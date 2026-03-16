from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from .config import settings
from .models import RefreshToken, Role, User, UserIdentity, UserRole
from .security import generate_refresh_token, hash_password, hash_refresh_token


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_identity_by_email(db: Session, email: str) -> UserIdentity | None:
    return (
        db.query(UserIdentity)
        .filter(
            UserIdentity.provider == "email",
            UserIdentity.provider_subject == email.lower(),
        )
        .first()
    )


def get_identity_by_telegram(db: Session, telegram_id: str) -> UserIdentity | None:
    return (
        db.query(UserIdentity)
        .filter(
            UserIdentity.provider == "telegram",
            UserIdentity.provider_subject == telegram_id,
        )
        .first()
    )


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.query(Role).filter(Role.name == name).first()


def create_user(db: Session, full_name: str, email: str, password: str) -> User:
    user = User(full_name=full_name)
    db.add(user)
    db.flush()

    identity = UserIdentity(
        user_id=user.id,
        provider="email",
        provider_subject=email.lower(),
        password_hash=hash_password(password),
        is_verified=False,
    )
    db.add(identity)

    role = get_role_by_name(db, "user")
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    db.commit()
    db.refresh(user)
    return user


def get_or_create_user_by_telegram(
    db: Session,
    telegram_id: str,
    telegram_username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    """Найти пользователя по telegram_id или создать нового (только Telegram, без email)."""
    identity = get_identity_by_telegram(db, telegram_id)
    if identity:
        user = get_user_by_id(db, identity.user_id)
        if user and user.is_active:
            return user

    parts = [p for p in [first_name, last_name] if p]
    full_name = " ".join(parts).strip() if parts else (telegram_username or f"tg_{telegram_id}")[:200]
    if not full_name:
        full_name = f"User {telegram_id}"[:200]

    user = User(full_name=full_name)
    db.add(user)
    db.flush()

    identity = UserIdentity(
        user_id=user.id,
        provider="telegram",
        provider_subject=telegram_id,
        is_verified=True,
    )
    db.add(identity)

    role = get_role_by_name(db, "user")
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    db.commit()
    db.refresh(user)
    return user


def link_telegram(
    db: Session, user_id: UUID, telegram_id: str, telegram_username: str | None
) -> UserIdentity:
    existing = get_identity_by_telegram(db, telegram_id)
    if existing:
        return existing

    identity = UserIdentity(
        user_id=user_id,
        provider="telegram",
        provider_subject=telegram_id,
        is_verified=True,
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity


def create_refresh_token(db: Session, user_id: UUID) -> str:
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_ttl_days)
    db.add(RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    db.commit()
    return raw_token


def get_refresh_token(db: Session, raw_token: str) -> RefreshToken | None:
    token_hash = hash_refresh_token(raw_token)
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .first()
    )


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hash_refresh_token(raw_token)
    token_obj = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )
    if token_obj:
        token_obj.revoked = True
        db.commit()


def get_user_roles(db: Session, user_id: UUID) -> list[str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    return [role.name for role in user.roles]


def get_user_primary_email(db: Session, user_id: UUID) -> str | None:
    identity = (
        db.query(UserIdentity)
        .filter(UserIdentity.user_id == user_id, UserIdentity.provider == "email")
        .first()
    )
    return identity.provider_subject if identity else None
