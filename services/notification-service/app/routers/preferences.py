from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import get_preferences, set_telegram_chat_id, upsert_preferences
from ..database import get_db
from ..schemas import PreferencesOut, PreferencesUpsert
from ..security import get_current_user_id

router = APIRouter(prefix="/notifications/preferences", tags=["preferences"])


@router.get("/me", response_model=PreferencesOut)
def get_my_preferences(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return the current user's notification preferences."""
    prefs = get_preferences(db, user_id)
    if not prefs:
        # Return safe defaults without persisting
        from ..models import NotificationPreference
        import uuid
        fake = NotificationPreference(
            id=uuid.uuid4(),
            user_id=user_id,
            email_enabled=True,
            telegram_enabled=False,
            telegram_chat_id=None,
            digest_enabled=True,
            digest_day_of_week=1,
        )
        from datetime import datetime
        fake.updated_at = datetime.utcnow()
        return fake
    return prefs


@router.put("/me", response_model=PreferencesOut)
def update_my_preferences(
    payload: PreferencesUpsert,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Upsert notification preferences for the current user."""
    return upsert_preferences(db, user_id, payload)


@router.post("/me/link-telegram", response_model=PreferencesOut)
def link_telegram(
    chat_id: int,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Bind a Telegram chat_id to the user's notification preferences.
    Called from the bot-service deep-link flow after /start.
    """
    return set_telegram_chat_id(db, user_id, chat_id)
