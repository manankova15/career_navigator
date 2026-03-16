"""
Recommendation orchestrator.

Flow:
  1. Fetch user's career profile + skills + preferences (profile-service).
  2. Fetch candidate vacancies filtered by preferred locations (vacancy-service).
  3. Call ml-service /ml/score → scored & ranked vacancies.
  4. Persist a new RecommendationSession + top-N VacancyRecommendations.
  5. Call ml-service /ml/skill-gap on the top recommendations.
  6. Persist SkillGapRecords for this session.
  7. Return the session.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .client import (
    call_skill_gap,
    call_scoring,
    fetch_candidate_vacancies,
    fetch_user_profile,
)
from .config import settings
from .crud import create_session, save_skill_gap
from .models import RecommendationSession

logger = logging.getLogger(__name__)


def _build_profile_input(profile: dict, prefs: dict, user_id: UUID) -> dict:
    return {
        "user_id": str(user_id),
        "skills": profile.get("skills", []),
        "preferred_locations": prefs.get("preferred_locations", []),
        "work_formats": prefs.get("work_formats", []),
        "target_roles": prefs.get("target_roles", []),
        "salary_from": prefs.get("salary_from"),
        "salary_to": prefs.get("salary_to"),
        "seniority": prefs.get("seniority"),
    }


def _vacancy_to_input(v: dict) -> dict:
    return {
        "vacancy_id": v["id"],
        "title": v.get("title", ""),
        "company": v.get("company", ""),
        "location": v.get("location"),
        "salary_from": v.get("salary_from"),
        "salary_to": v.get("salary_to"),
        "seniority": v.get("seniority"),
        "skills": v.get("skills", []),
        "employment_type": v.get("employment_type"),
    }


def run_recommendation(
    db: Session,
    user_id: UUID,
    user_token: str,
) -> RecommendationSession:
    # ── 1. Fetch profile ──────────────────────────────────────────────────
    try:
        raw_profile = fetch_user_profile(user_token)
    except Exception as exc:
        logger.error("Failed to fetch profile for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch user profile from profile-service",
        )

    prefs = raw_profile.get("preferences") or {}
    profile_input = _build_profile_input(raw_profile, prefs, user_id)

    preferred_locations = prefs.get("preferred_locations") or []
    primary_location = preferred_locations[0] if preferred_locations else None

    # ── 2. Fetch candidate vacancies ──────────────────────────────────────
    try:
        raw_vacancies = fetch_candidate_vacancies(
            location=primary_location,
            page_size=settings.vacancy_fetch_limit,
        )
    except Exception as exc:
        logger.error("Failed to fetch vacancies: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch vacancies from vacancy-service",
        )

    if not raw_vacancies:
        logger.warning("No candidate vacancies found for user=%s", user_id)

    vacancy_inputs = [_vacancy_to_input(v) for v in raw_vacancies]

    # ── 3. Score with ml-service ──────────────────────────────────────────
    try:
        score_resp = call_scoring({"profile": profile_input, "vacancies": vacancy_inputs})
    except Exception as exc:
        logger.error("ml-service /score failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scoring service unavailable",
        )

    results = score_resp.get("results", [])
    algorithm = score_resp.get("algorithm", "content_v1")
    total_scored = score_resp.get("total_scored", 0)

    # ── 4. Persist session + recommendations ──────────────────────────────
    session = create_session(
        db,
        user_id=user_id,
        algorithm=algorithm,
        total_scored=total_scored,
        scored_items=results[: settings.top_n_store],
    )

    # ── 5. Skill-gap on top recommendations ──────────────────────────────
    top_vacancy_ids = {str(r["vacancy_id"]) for r in results[:30]}
    top_vacancies_raw = [v for v in raw_vacancies if str(v["id"]) in top_vacancy_ids]
    top_vacancy_inputs = [_vacancy_to_input(v) for v in top_vacancies_raw]

    if top_vacancy_inputs:
        try:
            gap_resp = call_skill_gap(
                {"profile": profile_input, "target_vacancies": top_vacancy_inputs}
            )
            gaps = gap_resp.get("gaps", [])
            if gaps:
                save_skill_gap(db, session.id, user_id, gaps)
        except Exception as exc:
            logger.warning("Skill-gap call failed (non-fatal): %s", exc)

    logger.info(
        "Recommendation session created: user=%s session=%s scored=%d",
        user_id, session.id, total_scored,
    )
    return session
