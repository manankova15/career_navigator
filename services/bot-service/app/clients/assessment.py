"""Client for assessment-service."""
from __future__ import annotations

from ..config import settings
from .base import get_json, post_json


async def list_assessments(token: str, page_size: int = 8) -> list[dict]:
    try:
        data = await get_json(
            f"{settings.assessment_service_url}/assessments",
            token,
            params={"page_size": page_size},
        )
        return data.get("items", [])
    except Exception:
        return []


async def get_assessment(token: str, assessment_id: str) -> dict | None:
    """Fetch a single assessment with all items (answer options, no answer keys)."""
    try:
        return await get_json(
            f"{settings.assessment_service_url}/assessments/{assessment_id}",
            token,
        )
    except Exception:
        return None


async def submit_assessment(
    token: str,
    assessment_id: str,
    answers: list[dict],
) -> dict | None:
    """
    Submit all collected answers.
    answers = [{"item_id": str, "selected_option_ids": [str], "free_text": str | None}]
    """
    try:
        return await post_json(
            f"{settings.assessment_service_url}/assessments/{assessment_id}/submit",
            token,
            body={"answers": answers},
        )
    except Exception:
        return None


async def get_my_attempts(token: str, page_size: int = 5) -> list[dict]:
    try:
        data = await get_json(
            f"{settings.assessment_service_url}/attempts/me",
            token,
            params={"page_size": page_size},
        )
        return data.get("items", [])
    except Exception:
        return []
