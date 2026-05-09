"""
Recommendation orchestrator.

Refresh flow:
  1. Fetch profile (skills + preferences + likes enrichment).
  2. Fetch candidate vacancies from vacancy-service.
  3. Call ml-service /ml/score — purely deterministic AHP-weighted content match.
  4. Persist the session: VacancyRecommendation rows with `base_score` (content
     match) and `features` JSONB used later for live re-scoring.
  5. Apply personalization on top of the saved base_score and write the
     personalized value into `score` so the first /me read already reflects it.
  6. Call ml-service /ml/skill-gap on the top vacancies and persist results.

Read flow (/recommendations/me): see routers.recommendations — it always
re-scores live so that a new like, dislike or feedback event changes the
match percentages on the very next request.
"""

from __future__ import annotations

import logging
from collections import Counter
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
from .crud import create_session, get_active_likes, save_skill_gap, update_scores_in_place
from .models import RecommendationSession
from .personalization import build_affinity, score_with_personalization
from .profile_loader import load_profile_bundle

logger = logging.getLogger(__name__)


def _build_profile_input(profile: dict, prefs: dict, user_id: UUID) -> dict:
    target_roles = list(prefs.get("target_roles") or [])
    profile_target_role = profile.get("target_role")
    if profile_target_role and str(profile_target_role).strip():
        tr = str(profile_target_role).strip()
        if tr not in target_roles:
            target_roles.insert(0, tr)
    headline = profile.get("headline")
    if headline and str(headline).strip():
        h = str(headline).strip()
        if h not in target_roles:
            target_roles.append(h)

    return {
        "user_id": str(user_id),
        "skills": profile.get("skills", []),
        "preferred_locations": prefs.get("preferred_locations", []),
        "work_formats": prefs.get("work_formats", []),
        "target_roles": target_roles,
        "salary_from": prefs.get("salary_from"),
        "salary_to": prefs.get("salary_to"),
        "seniority": prefs.get("seniority"),
        "headline": profile.get("headline"),
        "summary": profile.get("summary"),
    }


def _enrich_profile_with_likes(db, user_id: UUID, profile_input: dict) -> None:
    likes = get_active_likes(db, user_id)
    skill_ctr: Counter[str] = Counter()
    titles: list[str] = []
    for lv in likes:
        for s in lv.vacancy_skills or []:
            if isinstance(s, str) and s.strip():
                skill_ctr[s.strip().lower()] += 1
        if lv.vacancy_title and str(lv.vacancy_title).strip():
            titles.append(str(lv.vacancy_title).strip())
    profile_input["liked_skills_top"] = [s for s, _ in skill_ctr.most_common(15)]
    profile_input["liked_titles"] = titles[:10]
    profile_input["total_likes"] = len(likes)


def _vacancy_to_input(v: dict) -> dict:
    pub = v.get("published_at")
    if pub is not None and hasattr(pub, "isoformat"):
        pub = pub.isoformat()
    desc = v.get("description")
    if desc and len(desc) > 8000:
        desc = desc[:8000]
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
        "description": desc or "",
        "published_at": pub,
    }


def _scored_to_db_item(r: dict) -> dict:
    features = dict(r.get("features") or {})
    return {
        "vacancy_id": r["vacancy_id"],
        "base_score": r["score"],
        "score": r["score"],   # will be overwritten after personalization
        "skill_score": r.get("skill_score", 0),
        "role_score": r.get("role_score", 0),
        "location_score": r.get("location_score", 0),
        "salary_score": r.get("salary_score", 0),
        "seniority_score": r.get("seniority_score", 0),
        "format_score": r.get("format_score", 0),
        "matched_skills": r.get("matched_skills", []),
        "missing_skills": r.get("missing_skills", []),
        "reasons": list(r.get("reasons") or []),
        "features": features,
    }


def run_recommendation_with_profile(
    db: Session,
    user_id: UUID,
    raw_profile: dict,
) -> RecommendationSession:
    prefs = raw_profile.get("preferences") or {}
    profile_input = _build_profile_input(raw_profile, prefs, user_id)
    _enrich_profile_with_likes(db, user_id, profile_input)

    preferred_locations = prefs.get("preferred_locations") or []
    primary_location = preferred_locations[0] if preferred_locations else None

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

    try:
        score_resp = call_scoring({"profile": profile_input, "vacancies": vacancy_inputs})
    except Exception as exc:
        logger.error("ml-service /score failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scoring service unavailable",
        )

    results = score_resp.get("results", [])
    algorithm = score_resp.get("algorithm", "content_ahp_v2")
    total_scored = score_resp.get("total_scored", 0)

    scored_items = [_scored_to_db_item(r) for r in results][: settings.top_n_store]

    session = create_session(
        db,
        user_id=user_id,
        algorithm=algorithm,
        total_scored=total_scored,
        scored_items=scored_items,
    )

    # ── Personalization pass ──
    affinity = build_affinity(db, user_id)
    personalized: dict[UUID, float] = {}
    for rec in session.recommendations:
        features = rec.features or {}
        final, _boost, _direct = score_with_personalization(
            affinity,
            base_score=float(rec.base_score),
            vacancy_id=rec.vacancy_id,
            vacancy_skills=list(features.get("vacancy_skills") or []),
            vacancy_title=features.get("vacancy_title") or "",
        )
        personalized[rec.id] = final
    update_scores_in_place(db, personalized)

    # ── Skill-gap on top-30 content vacancies (not personalized) ──
    top_ids = {str(r["vacancy_id"]) for r in results[:30]}
    top_vacancies_raw = [v for v in raw_vacancies if str(v["id"]) in top_ids]
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
        "Recommendation session created: user=%s session=%s scored=%d algorithm=%s signals=%d",
        user_id,
        session.id,
        total_scored,
        algorithm,
        affinity.total_signals,
    )
    return session


def run_recommendation(
    db: Session,
    user_id: UUID,
    user_token: str,
) -> RecommendationSession:
    try:
        raw_profile = fetch_user_profile(user_token)
    except Exception as exc:
        logger.error("Failed to fetch profile for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch user profile from profile-service",
        )
    return run_recommendation_with_profile(db, user_id, raw_profile)


def run_recommendation_from_db_profile(db: Session, user_id: UUID) -> RecommendationSession | None:
    raw = load_profile_bundle(db, user_id)
    if not raw:
        return None
    return run_recommendation_with_profile(db, user_id, raw)
