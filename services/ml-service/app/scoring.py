"""
Phase 1 — Content-based scoring engine.

Algorithm:
  score = w_skills * skill_score
        + w_location * location_score
        + w_salary * salary_score
        + w_seniority * seniority_score

Skill score: Jaccard similarity between user skill set and vacancy skill set.
Location: exact or partial match against user's preferred_locations; remote bonus.
Salary: whether vacancy range overlaps with user expectation.
Seniority: exact match or adjacent level tolerance.
"""

from __future__ import annotations

from .config import settings
from .schemas import ScoreRequest, ScoreResponse, ScoredVacancy, UserProfileInput, VacancyInput

SENIORITY_LEVELS = ["intern", "junior", "middle", "senior", "lead"]


def _skill_score(user_skills: set[str], vacancy_skills: set[str]) -> tuple[float, list[str], list[str]]:
    if not vacancy_skills:
        return 0.3, [], []   # neutral — vacancy has no skill requirements listed
    union = user_skills | vacancy_skills
    intersection = user_skills & vacancy_skills
    jaccard = len(intersection) / len(union) if union else 0.0
    matched = sorted(intersection)
    missing = sorted(vacancy_skills - user_skills)
    return round(jaccard, 4), matched, missing


def _location_score(profile: UserProfileInput, vacancy_location: str | None) -> float:
    if not vacancy_location:
        return 0.5   # no location data → neutral

    vac_loc = vacancy_location.lower()

    # Remote/hybrid vacancy → good for anyone
    if any(kw in vac_loc for kw in ("remote", "удалённ", "удален", "дистанц", "hybrid")):
        return 0.85

    if not profile.preferred_locations:
        return 0.5   # user has no preferences → neutral

    for pref in profile.preferred_locations:
        p = pref.lower()
        if p in vac_loc or vac_loc in p:
            return 1.0

    return 0.1   # location mismatch


def _salary_score(profile: UserProfileInput, vac_from: int | None, vac_to: int | None) -> float:
    if profile.salary_from is None and profile.salary_to is None:
        return 0.5   # user has no expectation → neutral
    if vac_from is None and vac_to is None:
        return 0.5   # vacancy has no salary info → neutral

    u_from = profile.salary_from or 0
    u_to = profile.salary_to or 10_000_000
    v_from = vac_from or 0
    v_to = vac_to or 10_000_000

    # Overlap between [u_from, u_to] and [v_from, v_to]
    overlap = max(0, min(u_to, v_to) - max(u_from, v_from))
    user_range = max(1, u_to - u_from)
    if overlap <= 0:
        # No overlap — check how far apart
        gap = max(u_from - v_to, v_from - u_to)
        if gap < u_from * 0.2:    # within 20% gap
            return 0.3
        return 0.1
    return min(1.0, round(overlap / user_range, 4))


def _seniority_score(profile: UserProfileInput, vacancy_seniority: str | None) -> float:
    if not vacancy_seniority or not profile.seniority:
        return 0.5   # neutral when one side is unknown

    u = profile.seniority.lower()
    v = vacancy_seniority.lower()

    if u == v:
        return 1.0

    try:
        u_idx = SENIORITY_LEVELS.index(u)
        v_idx = SENIORITY_LEVELS.index(v)
        diff = abs(u_idx - v_idx)
        if diff == 1:
            return 0.65  # adjacent level (e.g. junior↔middle)
        if diff == 2:
            return 0.30
    except ValueError:
        pass

    return 0.1


def _build_reasons(
    matched: list[str],
    loc_score: float,
    sal_score: float,
    sen_score: float,
    vacancy: VacancyInput,
) -> list[str]:
    reasons: list[str] = []
    if matched:
        preview = ", ".join(matched[:4])
        suffix = f" +{len(matched) - 4} more" if len(matched) > 4 else ""
        reasons.append(f"Skills match: {preview}{suffix}")
    if loc_score >= 0.85:
        reasons.append(f"Location fits: {vacancy.location or 'remote'}")
    if sal_score >= 0.8:
        reasons.append("Salary within expectation")
    if sen_score >= 0.9:
        reasons.append(f"Seniority match: {vacancy.seniority}")
    return reasons


def run_scoring(request: ScoreRequest) -> ScoreResponse:
    profile = request.profile
    user_skills = {s.strip().lower() for s in profile.skills}

    w = settings
    results: list[ScoredVacancy] = []

    for vac in request.vacancies[: w.max_candidates]:
        vac_skills = {s.strip().lower() for s in vac.skills}

        sk_score, matched, missing = _skill_score(user_skills, vac_skills)
        lo_score = _location_score(profile, vac.location)
        sa_score = _salary_score(profile, vac.salary_from, vac.salary_to)
        se_score = _seniority_score(profile, vac.seniority)

        total = (
            w.weight_skills * sk_score
            + w.weight_location * lo_score
            + w.weight_salary * sa_score
            + w.weight_seniority * se_score
        )

        results.append(
            ScoredVacancy(
                vacancy_id=vac.vacancy_id,
                score=round(total, 4),
                skill_score=sk_score,
                location_score=lo_score,
                salary_score=sa_score,
                seniority_score=se_score,
                matched_skills=matched,
                missing_skills=missing,
                reasons=_build_reasons(matched, lo_score, sa_score, se_score, vac),
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)

    return ScoreResponse(
        user_id=profile.user_id,
        algorithm="content_v1",
        total_scored=len(results),
        results=results[: w.top_n],
    )
