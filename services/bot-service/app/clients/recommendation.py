"""Client for recommendation-service."""
from __future__ import annotations

from ..config import settings
from .base import get_json, post_json


async def get_my_recommendations(token: str, page_size: int = 5) -> dict | None:
    try:
        return await get_json(
            f"{settings.recommendation_service_url}/recommendations/me",
            token,
            params={"page_size": page_size},
        )
    except Exception:
        return None


async def refresh_recommendations(token: str) -> dict | None:
    try:
        return await post_json(
            f"{settings.recommendation_service_url}/recommendations/refresh",
            token,
            body={},
        )
    except Exception:
        return None


async def get_skill_gap(token: str) -> dict | None:
    try:
        return await get_json(
            f"{settings.recommendation_service_url}/recommendations/skill-gap",
            token,
        )
    except Exception:
        return None


async def register_interaction(
    token: str,
    vacancy_id: str,
    sentiment: str,
    vacancy_title: str | None = None,
    vacancy_skills: list[str] | None = None,
    vacancy_category: str | None = None,
    vacancy_specialization: str | None = None,
) -> dict | None:
    """POST /recommendations/interactions/{vacancy_id} — 'interested' / 'not interested'."""
    try:
        return await post_json(
            f"{settings.recommendation_service_url}/recommendations/interactions/{vacancy_id}",
            token,
            body={
                "sentiment": sentiment,
                "source": "bot",
                "vacancy_title": vacancy_title,
                "vacancy_skills": vacancy_skills or [],
                "vacancy_category": vacancy_category,
                "vacancy_specialization": vacancy_specialization,
            },
        )
    except Exception:
        return None
