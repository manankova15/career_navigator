"""
Feature vectors for LightGBM ranker (subset of ml-recommendation-system-plan.md).
Order is stable — training and inference must use FEATURE_ORDER.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any

import numpy as np

from uuid import UUID

from ..scoring import SENIORITY_LEVELS, _location_score, _salary_score, _skill_score

_TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.I)


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    u = a | b
    if not u:
        return 0.0
    return len(a & b) / len(u)


def _salary_gap_normalized(profile: dict[str, Any], vacancy: dict[str, Any]) -> float:
    u_from = profile.get("salary_from") or 0
    u_to = profile.get("salary_to") or 10_000_000
    v_from = vacancy.get("salary_from") or 0
    v_to = vacancy.get("salary_to") or 10_000_000
    overlap = max(0, min(u_to, v_to) - max(u_from, v_from))
    if overlap > 0:
        return 0.0
    gap = max(u_from - v_to, v_from - u_to)
    denom = max(1, u_to - u_from)
    return float(min(1.0, gap / denom))


def _salary_above_expectation(profile: dict[str, Any], vacancy: dict[str, Any]) -> float:
    v_from = vacancy.get("salary_from")
    u_to = profile.get("salary_to")
    if v_from is not None and u_to is not None:
        return 1.0 if v_from > u_to else 0.0
    return 0.0


def _seniority_indices(profile: dict[str, Any], vacancy: dict[str, Any]) -> tuple[int | None, int | None]:
    u = (profile.get("seniority") or "").lower()
    v = (vacancy.get("seniority") or "").lower()
    try:
        return SENIORITY_LEVELS.index(u), SENIORITY_LEVELS.index(v)
    except ValueError:
        return None, None


def _vacancy_age_days(vacancy: dict[str, Any]) -> float:
    published = vacancy.get("published_at")
    if not published:
        return 0.0
    if isinstance(published, str):
        try:
            published = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    age = (now - published).days
    return float(min(max(age, 0), 90))


def _employment_type_match(profile: dict[str, Any], vacancy: dict[str, Any]) -> float:
    raw = vacancy.get("employment_type")
    if isinstance(raw, list):
        et = " ".join(str(x) for x in raw).lower()
    else:
        et = (raw or "").lower()
    if not et:
        return 0.5
    # No structured preference on profile — soft match on common tokens
    prefs = " ".join(profile.get("target_roles", []) or []).lower()
    if "part" in et and "part" in prefs:
        return 1.0
    if "full" in et:
        return 0.7
    return 0.5


def _work_format_match(profile: dict[str, Any], vacancy: dict[str, Any]) -> float:
    formats = [f.lower() for f in (profile.get("work_formats") or [])]
    loc = (vacancy.get("location") or "").lower()
    raw_wf = vacancy.get("work_format")
    if isinstance(raw_wf, list):
        vwf = " ".join(str(x) for x in raw_wf).lower()
    else:
        vwf = (raw_wf or "").lower()
    if not formats:
        return 0.5
    if "remote" in formats and (
        "remote" in vwf or any(k in loc for k in ("remote", "удалённ", "удален", "дистанц"))
    ):
        return 1.0
    if "hybrid" in formats and ("hybrid" in vwf or "hybrid" in loc):
        return 1.0
    if "office" in formats and formats == ["office"] and "remote" not in loc and "remote" not in vwf:
        return 0.8
    return 0.4


FEATURE_ORDER: list[str] = [
    "skill_jaccard",
    "skill_intersection_count",
    "skill_missing_count",
    "skill_weighted_match",
    "rare_skill_bonus",
    "salary_overlap_ratio",
    "salary_gap_normalized",
    "salary_above_expectation",
    "location_exact_match",
    "location_is_remote",
    "location_distance_km",
    "seniority_exact_match",
    "seniority_level_diff",
    "seniority_is_promotion",
    "title_similarity",
    "description_similarity",
    "vacancy_age_days",
    "company_size_category",
    "employment_type_match",
    "work_format_match",
    "user_total_interactions",
    "user_positive_rate",
    "vacancy_view_count",
    "vacancy_positive_rate",
    "similar_users_liked",
    "similar_users_avg_score",
    "user_assessment_avg_score",
    "skill_gap_overlap",
    "weak_skills_required",
    "strong_skills_match",
    "liked_skills_overlap",
    "liked_title_similarity",
    "has_likes",
    "content_baseline_score",
]


def _as_uuid(v: Any) -> UUID:
    return UUID(str(v))


class FeatureExtractor:
    def extract_row(
        self,
        profile: dict[str, Any],
        vacancy: dict[str, Any],
        user_stats: dict[str, Any] | None = None,
        vacancy_stats: dict[str, Any] | None = None,
        content_baseline_score: float = 0.0,
    ) -> np.ndarray:
        user_stats = user_stats or {}
        vacancy_stats = vacancy_stats or {}

        user_skills = {s.strip().lower() for s in profile.get("skills", [])}
        vac_skills = {s.strip().lower() for s in vacancy.get("skills", [])}
        sk_j, matched, missing = _skill_score(user_skills, vac_skills)
        intersection = user_skills & vac_skills

        from ..schemas import UserProfileInput, VacancyInput

        p_in = UserProfileInput(
            user_id=_as_uuid(profile["user_id"]),
            skills=profile.get("skills", []),
            preferred_locations=profile.get("preferred_locations", []),
            work_formats=profile.get("work_formats", []),
            target_roles=profile.get("target_roles", []),
            salary_from=profile.get("salary_from"),
            salary_to=profile.get("salary_to"),
            seniority=profile.get("seniority"),
            headline=profile.get("headline"),
            summary=profile.get("summary"),
            liked_skills_top=list(profile.get("liked_skills_top") or []),
            liked_titles=list(profile.get("liked_titles") or []),
            total_likes=int(profile.get("total_likes") or 0),
        )
        v_in = VacancyInput(
            vacancy_id=_as_uuid(vacancy["vacancy_id"]),
            title=vacancy.get("title", ""),
            company=vacancy.get("company", ""),
            location=vacancy.get("location"),
            salary_from=vacancy.get("salary_from"),
            salary_to=vacancy.get("salary_to"),
            seniority=vacancy.get("seniority"),
            skills=vacancy.get("skills", []),
            employment_type=vacancy.get("employment_type"),
            description=vacancy.get("description"),
            published_at=vacancy.get("published_at"),
        )
        loc_sc = float(_location_score(p_in, v_in.location))
        sal_overlap = float(_salary_score(p_in, v_in.salary_from, v_in.salary_to))
        loc_exact = 1.0 if loc_sc >= 0.99 else (0.7 if loc_sc >= 0.85 else 0.0)
        vac_loc = (vacancy.get("location") or "").lower()
        is_remote = 1.0 if any(k in vac_loc for k in ("remote", "удалённ", "удален", "дистанц")) else 0.0

        u_idx, v_idx = _seniority_indices(profile, vacancy)
        if u_idx is not None and v_idx is not None:
            sen_exact = 1.0 if u_idx == v_idx else 0.0
            sen_diff = abs(u_idx - v_idx) / max(1, len(SENIORITY_LEVELS) - 1)
            sen_promo = 1.0 if v_idx > u_idx else 0.0
        else:
            sen_exact = 0.5
            sen_diff = 0.5
            sen_promo = 0.0

        role_parts = list(profile.get("target_roles") or [])
        if profile.get("headline"):
            role_parts.append(str(profile["headline"]))
        if profile.get("summary"):
            role_parts.append(str(profile["summary"])[:200])
        role_blob = " ".join(role_parts)
        title_sim = _jaccard(_tokens(role_blob), _tokens(vacancy.get("title")))
        desc_sim = _jaccard(_tokens(role_blob), _tokens(vacancy.get("description")))

        weak_skills = float(len(missing)) / max(1, len(vac_skills)) if vac_skills else 0.0
        strong_skills = float(len(intersection)) / max(1, len(vac_skills)) if vac_skills else 0.0

        liked_skills = {str(s).strip().lower() for s in (profile.get("liked_skills_top") or []) if s}
        liked_titles_blob = " ".join(profile.get("liked_titles") or [])
        liked_skills_overlap = _jaccard(liked_skills, vac_skills) if liked_skills else 0.0
        liked_title_sim = (
            _jaccard(_tokens(liked_titles_blob), _tokens(vacancy.get("title")))
            if liked_titles_blob.strip()
            else 0.0
        )
        has_likes = 1.0 if int(profile.get("total_likes") or 0) > 0 else 0.0

        values: dict[str, float] = {
            "skill_jaccard": float(sk_j),
            "skill_intersection_count": float(len(intersection)),
            "skill_missing_count": float(len(missing)),
            "skill_weighted_match": float(sk_j),
            "rare_skill_bonus": 0.0,
            "salary_overlap_ratio": sal_overlap,
            "salary_gap_normalized": _salary_gap_normalized(profile, vacancy),
            "salary_above_expectation": _salary_above_expectation(profile, vacancy),
            "location_exact_match": loc_exact,
            "location_is_remote": is_remote,
            "location_distance_km": 0.0,
            "seniority_exact_match": sen_exact,
            "seniority_level_diff": float(sen_diff),
            "seniority_is_promotion": float(sen_promo),
            "title_similarity": float(title_sim),
            "description_similarity": float(desc_sim),
            "vacancy_age_days": _vacancy_age_days(vacancy),
            "company_size_category": 0.0,
            "employment_type_match": _employment_type_match(profile, vacancy),
            "work_format_match": _work_format_match(profile, vacancy),
            "user_total_interactions": float(user_stats.get("total_interactions", 0)),
            "user_positive_rate": float(user_stats.get("positive_rate", 0.5)),
            "vacancy_view_count": float(vacancy_stats.get("view_count", 0)),
            "vacancy_positive_rate": float(vacancy_stats.get("positive_rate", 0.5)),
            "similar_users_liked": float(vacancy_stats.get("similar_users_liked", 0)),
            "similar_users_avg_score": float(vacancy_stats.get("similar_users_avg_score", 0.5)),
            "user_assessment_avg_score": float(user_stats.get("assessment_avg_score", 0.5)),
            "skill_gap_overlap": float(user_stats.get("skill_gap_overlap", 0.0)),
            "weak_skills_required": weak_skills,
            "strong_skills_match": strong_skills,
            "liked_skills_overlap": float(liked_skills_overlap),
            "liked_title_similarity": float(liked_title_sim),
            "has_likes": float(has_likes),
            "content_baseline_score": float(content_baseline_score),
        }
        return np.array([values[name] for name in FEATURE_ORDER], dtype=np.float64)

    def build_matrix(
        self,
        profile: dict[str, Any],
        vacancies: list[dict[str, Any]],
        content_scores: dict[str, float],
        user_stats: dict[str, Any] | None = None,
        vacancy_stats_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> np.ndarray:
        vacancy_stats_by_id = vacancy_stats_by_id or {}
        rows = []
        for vac in vacancies:
            vid = str(vac["vacancy_id"])
            cb = content_scores.get(vid, 0.0)
            vs = vacancy_stats_by_id.get(vid, {})
            rows.append(self.extract_row(profile, vac, user_stats, vs, cb))
        return np.vstack(rows) if rows else np.zeros((0, len(FEATURE_ORDER)), dtype=np.float64)


def minmax_norm(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return arr
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if math.isclose(hi, lo):
        return np.ones_like(arr) * 0.5
    return (arr - lo) / (hi - lo)
