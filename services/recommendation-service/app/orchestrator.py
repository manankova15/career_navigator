"""
Recommendation orchestrator — версия алгоритма ``hybrid_ahp_v3``.

Pipeline /refresh:
  1. Загружаем профиль (skills + preferences + likes-обогащение).
  2. Собираем AffinityProfile (личная история сигналов с time-decay и
     байесовским shrinkage — см. personalization.py).
  3. Тянем кандидатов из vacancy-service.
  4. Зовём ml-service /ml/score, передавая профиль, вакансии **и** behavior-блок
     (категории/специализации/навыки/тайтлы + множества V⁺/V⁻ + N сигналов).
     Алгоритм считает S(u, v) = (1−τ)P + τB c мультипликатором и прямыми
     override-ами (полная формула — в docs/recommendation_model_v3.md).
  5. Сохраняем результат в БД с расширенным набором фич; повторный
     персонализационный проход не нужен — ml-service уже учёл affinity.
  6. Считаем skill-gap по топ-30.

Pipeline /me — лёгкий live-rescore (см. routers.recommendations._live_rescore):
любая свежая реакция пользователя меняет AffinityProfile, и тот же скор
пересчитывается без обращения к ml-сервису.
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
from .crud import create_session, get_active_likes, save_skill_gap
from .models import RecommendationSession
from .personalization import AffinityProfile, build_affinity
from .profile_loader import load_profile_bundle

logger = logging.getLogger(__name__)


# Маппинг канонических кодов городов (из CITIES в frontend) на русские
# названия, которые реально хранятся в vacancy-service (location_city).
# Нужен, чтобы location_score в ml-service мог сматчить подстрокой.
_CITY_CODE_TO_RU: dict[str, str] = {
    "remote": "удалённо",
    "moscow": "Москва",
    "spb": "Санкт-Петербург",
    "novosibirsk": "Новосибирск",
    "ekaterinburg": "Екатеринбург",
    "kazan": "Казань",
    "nizhny-novgorod": "Нижний Новгород",
    "chelyabinsk": "Челябинск",
    "samara": "Самара",
    "rostov-on-don": "Ростов-на-Дону",
    "ufa": "Уфа",
    "krasnoyarsk": "Красноярск",
    "perm": "Пермь",
    "voronezh": "Воронеж",
    "volgograd": "Волгоград",
    "krasnodar": "Краснодар",
    "saratov": "Саратов",
    "tyumen": "Тюмень",
    "tolyatti": "Тольятти",
    "izhevsk": "Ижевск",
    "barnaul": "Барнаул",
    "ulyanovsk": "Ульяновск",
    "irkutsk": "Иркутск",
    "khabarovsk": "Хабаровск",
    "yaroslavl": "Ярославль",
    "vladivostok": "Владивосток",
    "makhachkala": "Махачкала",
    "tomsk": "Томск",
    "orenburg": "Оренбург",
    "kemerovo": "Кемерово",
    "novokuznetsk": "Новокузнецк",
    "ryazan": "Рязань",
    "astrakhan": "Астрахань",
    "naberezhnye-chelny": "Набережные Челны",
    "penza": "Пенза",
    "lipetsk": "Липецк",
    "kirov": "Киров",
    "cheboksary": "Чебоксары",
    "tula": "Тула",
    "kaliningrad": "Калининград",
    "balashikha": "Балашиха",
    "kursk": "Курск",
    "stavropol": "Ставрополь",
    "ulan-ude": "Улан-Удэ",
    "tver": "Тверь",
    "magnitogorsk": "Магнитогорск",
    "sochi": "Сочи",
    "ivanovo": "Иваново",
    "bryansk": "Брянск",
    "belgorod": "Белгород",
    "surgut": "Сургут",
    "vladimir": "Владимир",
    "nizhny-tagil": "Нижний Тагил",
    "arkhangelsk": "Архангельск",
    "chita": "Чита",
    "kaluga": "Калуга",
    "smolensk": "Смоленск",
    "volzhsky": "Волжский",
    "kurgan": "Курган",
    "oryol": "Орёл",
    "cherepovets": "Череповец",
    "vologda": "Вологда",
    "saransk": "Саранск",
    "murmansk": "Мурманск",
}


def _location_code_to_label(code: str | None) -> str | None:
    if not code:
        return None
    return _CITY_CODE_TO_RU.get(code, code)


def _build_profile_input(profile: dict, prefs: dict, user_id: UUID) -> dict:
    """После v2 пользователь сам выбирает канонические коды специализации,
    профессиональной области и города в форме профиля. Никакого regex-
    классификатора уже не требуется — коды кладутся в скоринг напрямую."""
    target_industry = profile.get("target_industry")
    specialization = profile.get("specialization")
    location_code = profile.get("location")
    location_label = _location_code_to_label(location_code)

    preferred_categories: list[str] = [target_industry] if target_industry else []
    preferred_specializations: list[str] = [specialization] if specialization else []
    preferred_locations: list[str] = [location_label] if location_label else []

    return {
        "user_id": str(user_id),
        "skills": profile.get("skills", []),
        "preferred_locations": preferred_locations,
        "work_formats": prefs.get("work_formats", []),
        "salary_from": prefs.get("salary_from"),
        "salary_to": prefs.get("salary_to"),
        "seniority": prefs.get("seniority"),
        "target_industry": target_industry,
        "preferred_categories": preferred_categories,
        "preferred_specializations": preferred_specializations,
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
    # Для скоринга используем рублёвый эквивалент: пользователь выбирает
    # ожидаемую зарплату в рублях, а у вакансий теперь могут быть USD/EUR/...
    salary_from = v.get("salary_from_rub") or v.get("salary_from")
    salary_to = v.get("salary_to_rub") or v.get("salary_to")
    return {
        "vacancy_id": v["id"],
        "title": v.get("title", ""),
        "company": v.get("company", ""),
        "location": v.get("location"),
        "salary_from": salary_from,
        "salary_to": salary_to,
        "seniority": v.get("seniority"),
        "skills": v.get("skills", []),
        "employment_type": (
            ", ".join(v.get("employment_type") or [])
            if isinstance(v.get("employment_type"), list)
            else v.get("employment_type")
        ),
        "description": desc or "",
        "published_at": pub,
        "profession_area": v.get("profession_area"),
        "specialization": v.get("specialization"),
        "work_format": list(v.get("work_format") or []),
    }


def _scored_to_db_item(r: dict) -> dict:
    features = dict(r.get("features") or {})
    return {
        "vacancy_id": r["vacancy_id"],
        "base_score": r.get("base_score", r["score"]),
        "score": r["score"],
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


def _affinity_to_payload(aff: AffinityProfile) -> dict:
    return aff.to_behavior_payload()


def run_recommendation_with_profile(
    db: Session,
    user_id: UUID,
    raw_profile: dict,
) -> RecommendationSession:
    prefs = raw_profile.get("preferences") or {}
    profile_input = _build_profile_input(raw_profile, prefs, user_id)
    _enrich_profile_with_likes(db, user_id, profile_input)

    affinity = build_affinity(db, user_id)

    # Note: we intentionally do NOT pre-filter candidate vacancies by location.
    # Profile stores canonical city codes ("moscow", "spb"), while vacancy DB
    # stores Russian city names ("Москва", "Санкт-Петербург"). Pre-filtering
    # would yield 0 matches. Location is already a scoring feature in ml-service
    # (location_score, weight ≈ 0.02), so ranking handles geographic preference.
    try:
        raw_vacancies = fetch_candidate_vacancies(
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
    behavior_payload = _affinity_to_payload(affinity)

    try:
        score_resp = call_scoring(
            {
                "profile": profile_input,
                "vacancies": vacancy_inputs,
                "behavior": behavior_payload,
            }
        )
    except Exception as exc:
        logger.error("ml-service /score failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scoring service unavailable",
        )

    results = score_resp.get("results", [])
    algorithm = score_resp.get("algorithm", "hybrid_ahp_v3")
    total_scored = score_resp.get("total_scored", 0)

    scored_items = [_scored_to_db_item(r) for r in results][: settings.top_n_store]

    # Guard: never persist an empty session – it would shadow any older, useful
    # session for the user and break the "refresh-on-404" path on the frontend
    # (the API would keep returning HTTP 200 with items=[]). Treat empty result
    # as a transient failure of the upstream pipeline (vacancy-service returned
    # no candidates, ml-service produced no scores, network blip, etc.) and
    # surface it as 502 so the caller can retry. Scheduled refresh in
    # scheduler_jobs.py already catches and logs such exceptions.
    if not scored_items or total_scored == 0:
        logger.warning(
            "Skipping persistence of empty recommendation session for user=%s "
            "(raw_vacancies=%d, results=%d, total_scored=%d)",
            user_id,
            len(raw_vacancies),
            len(results),
            total_scored,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Recommendation pipeline produced no results; please retry later",
        )

    session = create_session(
        db,
        user_id=user_id,
        algorithm=algorithm,
        total_scored=total_scored,
        scored_items=scored_items,
    )

    # ── Skill-gap on top-30 content vacancies ──
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
        "Recommendation session created: user=%s session=%s scored=%d algorithm=%s "
        "signals=%d trust=%.2f",
        user_id,
        session.id,
        total_scored,
        algorithm,
        affinity.total_signals,
        affinity.trust,
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
