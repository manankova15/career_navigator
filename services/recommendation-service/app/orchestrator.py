"""
Recommendation orchestrator.

Flow:
  1. Fetch user's career profile + skills + preferences (profile-service or DB).
  2. Fetch candidate vacancies filtered by preferred locations (vacancy-service).
  3. Call ml-service /ml/score → content-based scores.
  4. Call ml-service /ml/rank → hybrid LightGBM re-ranking (fallback: content order).
  5. Persist a new RecommendationSession + top-N VacancyRecommendations.
  6. Call ml-service /ml/skill-gap on the top recommendations.
  7. Persist SkillGapRecords for this session.
"""

from __future__ import annotations

import logging
from collections import Counter
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .client import (
    call_rank,
    call_skill_gap,
    call_scoring,
    fetch_candidate_vacancies,
    fetch_user_profile,
)
from .config import settings
from .crud import create_session, get_active_likes, save_skill_gap
from .models import RecommendationSession
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


def _vacancy_fallback_for_rank(r: dict) -> dict:
    return {
        "vacancy_id": r["vacancy_id"],
        "title": "",
        "company": "",
        "location": None,
        "salary_from": None,
        "salary_to": None,
        "seniority": None,
        "skills": [],
        "employment_type": None,
        "description": "",
        "published_at": None,
    }


def _merge_rank_into_session_items(rank_results: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in rank_results:
        reasons = list(r.get("reasons") or [])
        expl = r.get("rank_explanation") or []
        if expl:
            reasons = reasons + [str(x) for x in expl]
        out.append(
            {
                "vacancy_id": r["vacancy_id"],
                "score": r["score"],
                "skill_score": r.get("skill_score", 0),
                "location_score": r.get("location_score", 0),
                "salary_score": r.get("salary_score", 0),
                "seniority_score": r.get("seniority_score", 0),
                "matched_skills": r.get("matched_skills", []),
                "missing_skills": r.get("missing_skills", []),
                "reasons": reasons,
                "ml_score": r.get("ml_score"),
            }
        )
    return out


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
    algorithm = score_resp.get("algorithm", "content_v1")
    total_scored = score_resp.get("total_scored", 0)

    vac_by_id = {str(v["id"]): v for v in raw_vacancies}
    rank_vacancies: list[dict] = []
    for r in results:
        vid = str(r["vacancy_id"])
        raw = vac_by_id.get(vid)
        rank_vacancies.append(_vacancy_to_input(raw) if raw else _vacancy_fallback_for_rank(r))

    final_results: list[dict] = results
    if results:
        try:
            rank_resp = call_rank(
                {
                    "profile": profile_input,
                    "vacancies": rank_vacancies,
                    "content_results": results,
                }
            )
            final_results = rank_resp.get("results", results)
            algorithm = rank_resp.get("algorithm", algorithm)
        except Exception as exc:
            logger.warning("ml-service /rank failed (using content order): %s", exc)

    scored_items = _merge_rank_into_session_items(final_results)[: settings.top_n_store]

    session = create_session(
        db,
        user_id=user_id,
        algorithm=algorithm,
        total_scored=total_scored,
        scored_items=scored_items,
    )

    top_vacancy_ids = {str(r["vacancy_id"]) for r in final_results[:30]}
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
        "Recommendation session created: user=%s session=%s scored=%d algorithm=%s",
        user_id,
        session.id,
        total_scored,
        algorithm,
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
