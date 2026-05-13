"""
Personalization layer for recommendation model ``hybrid_ahp_v3``.

Полное математическое обоснование — в ``docs/recommendation_model_v3.md``.

Здесь решаются две задачи:

1. **Сборка AffinityProfile** из всех сигналов пользователя
   (UserLikedVacancy + UserVacancySignal + VacancyRecommendation.feedback)
   с временным затуханием и байесовским сглаживанием:

      θ_x[k] = Σ_j r_j ω(Δt_j) / (Σ_j ω(Δt_j) + λ_x),
      ω(Δt) = 2^(−Δt / T_½), T_½ = 90 дней.

2. **Скоринг live** по тем же формулам, которые применяет ml-service: это
   нужно, чтобы любой свежий лайк/кнопка отражались на следующем GET /me без
   обращения к ml-сервису. ML-сервис всё равно вызывается на /refresh и
   является source-of-truth для алгоритма.
"""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from .models import UserLikedVacancy, UserVacancySignal, VacancyRecommendation

logger = logging.getLogger(__name__)


# ── Гиперпараметры (синхронизированы с ml-service/app/config.py) ────────────

# Период полураспада значимости сигнала.
TIME_DECAY_HALF_LIFE_DAYS = 90.0

# Байесовский shrinkage для каждой оси: чем больше — тем сильнее «сжимаем» к 0.
SHRINKAGE_CATEGORY = 1.0
SHRINKAGE_SPECIALIZATION = 1.0
SHRINKAGE_SKILL = 2.0
SHRINKAGE_TITLE = 3.0

# Веса осей в поведенческом скоре B(u, v). Сумма = 1.
ALPHA_CATEGORY = 0.32
ALPHA_SPECIALIZATION = 0.32
ALPHA_SKILLS = 0.22
ALPHA_TITLE = 0.14

# τ(N) = N / (N + N0). См. §5 модели v3.
BEHAVIOR_TRUST_N0 = 5.0

# Прямой override.
DIRECT_POSITIVE_FLOOR = 0.95
DIRECT_NEGATIVE_CEILING = 0.15
DIRECT_NEGATIVE_MULTIPLIER = 0.10
POS_SENTIMENT_THRESHOLD = 0.999
NEG_SENTIMENT_THRESHOLD = -0.999

# Мультипликатор M(u, v).
MULT_MIN = 0.20
MULT_MAX = 1.50
MULT_SKILL_REWARD = 0.35
MULT_TITLE_REWARD = 0.25
MULT_SKILL_PENALTY = 0.80
MULT_TITLE_PENALTY = 0.55
POS_SKILL_THRESHOLD = 0.20
NEG_SKILL_THRESHOLD = -0.20


_TOKEN_RE = re.compile(r"[a-zа-яё0-9+#\.]+", re.I)
_STOPWORDS = {
    "и", "в", "на", "с", "для", "of", "the", "a", "an", "to", "in", "at",
    "по", "от", "или", "or", "and", "for", "into", "из",
}


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        m.group(0).lower()
        for m in _TOKEN_RE.finditer(text)
        if len(m.group(0)) > 1 and m.group(0).lower() not in _STOPWORDS
    }


def _norm_label(value: str | None) -> str | None:
    if not value:
        return None
    s = str(value).strip().lower()
    return s or None


def _decay_weight(event_time: datetime | None, now: datetime) -> float:
    """ω(Δt) = 2^(−Δt / T_½). При отсутствии времени считаем «свежим» (1.0)."""
    if event_time is None:
        return 1.0
    delta = (now - event_time).total_seconds() / 86400.0
    if delta < 0:
        delta = 0.0
    return math.pow(2.0, -delta / TIME_DECAY_HALF_LIFE_DAYS)


# ── AffinityProfile ─────────────────────────────────────────────────────────

@dataclass
class AffinityProfile:
    """Сглаженные предпочтения пользователя по 4 осям + множества прямых
    положительных/отрицательных вакансий + общее число сигналов N_u."""

    category_pref: dict[str, float] = field(default_factory=dict)
    specialization_pref: dict[str, float] = field(default_factory=dict)
    skill_pref: dict[str, float] = field(default_factory=dict)
    title_token_pref: dict[str, float] = field(default_factory=dict)
    positive_vacancy_ids: set[str] = field(default_factory=set)
    negative_vacancy_ids: set[str] = field(default_factory=set)
    total_signals: int = 0

    @property
    def trust(self) -> float:
        n = max(0, int(self.total_signals))
        return n / (n + BEHAVIOR_TRUST_N0) if (n + BEHAVIOR_TRUST_N0) > 0 else 0.0

    def top_categories(self, n: int = 5) -> list[str]:
        return [
            k for k, v in sorted(self.category_pref.items(), key=lambda kv: kv[1], reverse=True)[:n]
            if v > 0
        ]

    def top_specializations(self, n: int = 5) -> list[str]:
        return [
            k for k, v in sorted(self.specialization_pref.items(), key=lambda kv: kv[1], reverse=True)[:n]
            if v > 0
        ]

    def top_skills(self, n: int = 10) -> list[str]:
        return [
            k for k, v in sorted(self.skill_pref.items(), key=lambda kv: kv[1], reverse=True)[:n]
            if v > 0
        ]

    def top_title_tokens(self, n: int = 10) -> list[str]:
        return [
            k for k, v in sorted(self.title_token_pref.items(), key=lambda kv: kv[1], reverse=True)[:n]
            if v > 0
        ]

    def to_behavior_payload(self) -> dict:
        """Сериализация в dict, который ml-service ожидает в ScoreRequest.behavior."""
        return {
            "total_signals": int(self.total_signals),
            "category_pref": {k: round(float(v), 4) for k, v in self.category_pref.items()},
            "specialization_pref": {k: round(float(v), 4) for k, v in self.specialization_pref.items()},
            "skill_pref": {k: round(float(v), 4) for k, v in self.skill_pref.items()},
            "title_token_pref": {k: round(float(v), 4) for k, v in self.title_token_pref.items()},
            "positive_vacancy_ids": sorted(self.positive_vacancy_ids),
            "negative_vacancy_ids": sorted(self.negative_vacancy_ids),
        }


@dataclass
class _Aggregator:
    s_sum: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    w_sum: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def add(self, key: str, sentiment: float, weight: float) -> None:
        if not key or weight <= 0:
            return
        self.s_sum[key] += sentiment * weight
        self.w_sum[key] += weight

    def shrink(self, lam: float) -> dict[str, float]:
        out: dict[str, float] = {}
        for k, s in self.s_sum.items():
            w = self.w_sum.get(k, 0.0)
            if w <= 0:
                continue
            theta = s / (w + lam)
            out[k] = max(-1.0, min(1.0, theta))
        return out


def _ingest_signal(
    cat_agg: _Aggregator,
    spec_agg: _Aggregator,
    skill_agg: _Aggregator,
    title_agg: _Aggregator,
    sentiment: float,
    weight: float,
    category: str | None,
    specialization: str | None,
    skills: Iterable[str],
    title: str | None,
) -> None:
    cat = _norm_label(category)
    spec = _norm_label(specialization)
    if cat:
        cat_agg.add(cat, sentiment, weight)
    if spec:
        spec_agg.add(spec, sentiment, weight)
    for s in skills or []:
        key = _norm_label(s)
        if key:
            skill_agg.add(key, sentiment, weight)
    for t in _tokens(title or ""):
        title_agg.add(t, sentiment, weight)


def build_affinity(db: Session, user_id: UUID, now: datetime | None = None) -> AffinityProfile:
    """Соберём AffinityProfile из всех источников сигналов.

    Источники:
      • UserLikedVacancy (активные лайки) → r = +1.
      • UserVacancySignal (явные кнопки)  → r = sentiment ∈ {−1, 0, +1}.
      • VacancyRecommendation.feedback     → r ∈ {+1, 0, −1} (positive/saved/negative).

    К каждому событию применяется временное затухание ω(Δt) = 2^(−Δt/T_½).
    Сглаженные предпочтения θ_x вычисляются с λ-shrinkage (см. §4.3 v3).
    """
    now = now or datetime.utcnow()

    cat_agg = _Aggregator()
    spec_agg = _Aggregator()
    skill_agg = _Aggregator()
    title_agg = _Aggregator()

    profile = AffinityProfile()

    # 1) UserLikedVacancy
    try:
        active_likes = (
            db.query(UserLikedVacancy)
            .filter(
                UserLikedVacancy.user_id == user_id,
                UserLikedVacancy.unliked_at.is_(None),
            )
            .all()
        )
    except ProgrammingError as exc:
        logger.warning("user_liked_vacancies query failed (missing migration?): %s", exc)
        db.rollback()
        active_likes = []
    for lv in active_likes:
        weight = _decay_weight(lv.liked_at, now)
        _ingest_signal(
            cat_agg, spec_agg, skill_agg, title_agg,
            sentiment=1.0,
            weight=weight,
            category=lv.vacancy_category,
            specialization=lv.vacancy_specialization,
            skills=list(lv.vacancy_skills or []),
            title=lv.vacancy_title,
        )
        profile.positive_vacancy_ids.add(str(lv.vacancy_id))
        profile.total_signals += 1

    # 2) UserVacancySignal
    try:
        signals = (
            db.query(UserVacancySignal)
            .filter(UserVacancySignal.user_id == user_id)
            .all()
        )
    except ProgrammingError as exc:
        logger.warning(
            "user_vacancy_signals query failed — run `make migrate-recommendation`: %s",
            exc,
        )
        db.rollback()
        signals = []
    for sig in signals:
        sentiment = float(sig.sentiment or 0.0)
        if abs(sentiment) < 1e-6:
            # nb: «нейтральный» сигнал (просмотр) повышает N_u, но не двигает θ.
            profile.total_signals += 1
            continue
        weight = _decay_weight(sig.updated_at or sig.created_at, now)
        _ingest_signal(
            cat_agg, spec_agg, skill_agg, title_agg,
            sentiment=sentiment,
            weight=weight,
            category=sig.vacancy_category,
            specialization=sig.vacancy_specialization,
            skills=list(sig.vacancy_skills or []),
            title=sig.vacancy_title,
        )
        if sentiment >= POS_SENTIMENT_THRESHOLD:
            profile.positive_vacancy_ids.add(str(sig.vacancy_id))
        elif sentiment <= NEG_SENTIMENT_THRESHOLD:
            profile.negative_vacancy_ids.add(str(sig.vacancy_id))
        profile.total_signals += 1

    # 3) Старый канал — feedback в VacancyRecommendation. Мы уже зеркалим
    #    его в user_vacancy_signals через apply_feedback, но для исторических
    #    данных (до миграции 005) фактический снапшот категории/специализации
    #    лежит только в features. Берём именно оттуда.
    try:
        feedback_rows = (
            db.query(VacancyRecommendation)
            .filter(
                VacancyRecommendation.user_id == user_id,
                VacancyRecommendation.feedback.isnot(None),
            )
            .all()
        )
    except ProgrammingError as exc:
        logger.warning("vacancy_recommendations query failed: %s", exc)
        db.rollback()
        feedback_rows = []
    seen_legacy: set[str] = set()
    for rec in feedback_rows:
        # Если по этой вакансии уже есть запись в user_vacancy_signals,
        # пропускаем — иначе двойной счёт.
        vid = str(rec.vacancy_id)
        if vid in seen_legacy:
            continue
        seen_legacy.add(vid)
        if vid in profile.positive_vacancy_ids or vid in profile.negative_vacancy_ids:
            continue
        if rec.feedback == "positive":
            sentiment = 1.0
        elif rec.feedback == "negative":
            sentiment = -1.0
        elif rec.feedback == "saved":
            sentiment = 0.5
        else:
            continue
        weight = _decay_weight(rec.feedback_at or rec.created_at, now)
        features = rec.features or {}
        _ingest_signal(
            cat_agg, spec_agg, skill_agg, title_agg,
            sentiment=sentiment,
            weight=weight,
            category=features.get("vacancy_category"),
            specialization=features.get("vacancy_specialization"),
            skills=list(features.get("vacancy_skills") or rec.matched_skills or []),
            title=features.get("vacancy_title"),
        )
        if sentiment >= POS_SENTIMENT_THRESHOLD:
            profile.positive_vacancy_ids.add(vid)
        elif sentiment <= NEG_SENTIMENT_THRESHOLD:
            profile.negative_vacancy_ids.add(vid)
        profile.total_signals += 1

    profile.category_pref = cat_agg.shrink(SHRINKAGE_CATEGORY)
    profile.specialization_pref = spec_agg.shrink(SHRINKAGE_SPECIALIZATION)
    profile.skill_pref = skill_agg.shrink(SHRINKAGE_SKILL)
    profile.title_token_pref = title_agg.shrink(SHRINKAGE_TITLE)

    return profile


# ── Live B(u, v), M(u, v) и financial blend ─────────────────────────────────

def _avg_pref(keys: Iterable[str], pref_map: dict[str, float]) -> float:
    vals = [pref_map[k] for k in keys if k in pref_map]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def behavior_score_live(
    affinity: AffinityProfile,
    vacancy_category: str | None,
    vacancy_specialization: str | None,
    vacancy_skills: Iterable[str],
    vacancy_title: str | None,
) -> float:
    """B(u, v) ∈ [0, 1] — без обращения в ml-service."""
    cat = _norm_label(vacancy_category)
    spec = _norm_label(vacancy_specialization)
    skills = {_norm_label(s) for s in (vacancy_skills or []) if s}
    skills = {s for s in skills if s}
    tokens = _tokens(vacancy_title or "")

    beta_c = affinity.category_pref.get(cat, 0.0) if cat else 0.0
    beta_s = affinity.specialization_pref.get(spec, 0.0) if spec else 0.0
    beta_sk = _avg_pref(skills, affinity.skill_pref)
    beta_t = _avg_pref(tokens, affinity.title_token_pref)

    s = (
        ALPHA_CATEGORY * beta_c
        + ALPHA_SPECIALIZATION * beta_s
        + ALPHA_SKILLS * beta_sk
        + ALPHA_TITLE * beta_t
    )
    return max(0.0, min(1.0, 0.5 + 0.5 * s))


def multiplier_live(
    affinity: AffinityProfile,
    vacancy_skills: Iterable[str],
    vacancy_title: str | None,
) -> float:
    """M(u, v) ∈ [MULT_MIN, MULT_MAX]."""
    tau = affinity.trust
    if tau <= 0.0:
        return 1.0

    skills = [s for s in ({_norm_label(x) for x in (vacancy_skills or []) if x}) if s]
    if skills:
        per = [affinity.skill_pref.get(s, 0.0) for s in skills]
        n = len(per)
        neg_skill = sum(1 for v in per if v <= NEG_SKILL_THRESHOLD) / n
        pos_skill = sum(1 for v in per if v >= POS_SKILL_THRESHOLD) / n
    else:
        neg_skill = pos_skill = 0.0

    tokens = _tokens(vacancy_title or "")
    if tokens:
        per_t = [affinity.title_token_pref.get(t, 0.0) for t in tokens]
        n = len(per_t)
        neg_title = sum(1 for v in per_t if v <= NEG_SKILL_THRESHOLD) / n
        pos_title = sum(1 for v in per_t if v >= POS_SKILL_THRESHOLD) / n
    else:
        neg_title = pos_title = 0.0

    reward = MULT_SKILL_REWARD * pos_skill + MULT_TITLE_REWARD * pos_title
    penalty = MULT_SKILL_PENALTY * neg_skill + MULT_TITLE_PENALTY * neg_title
    mult = 1.0 + tau * (reward - penalty)
    return max(MULT_MIN, min(MULT_MAX, mult))


def score_with_personalization(
    affinity: AffinityProfile,
    base_score: float,
    vacancy_id: str | UUID,
    vacancy_skills: list[str],
    vacancy_title: str,
    vacancy_category: str | None = None,
    vacancy_specialization: str | None = None,
) -> tuple[float, float, float | None]:
    """Полный live-скор для одной вакансии.

    Возвращает кортеж ``(final_score, soft_boost, direct_signal)``:

      * ``final_score`` ∈ [0, 1] — то, что покажем в UI;
      * ``soft_boost`` — поведенческий вклад относительно профиля
        (для отображения «насколько персонализация подняла/опустила вакансию»);
      * ``direct_signal`` — +1/−1/None в зависимости от того, оценена ли уже
        эта вакансия пользователем напрямую.
    """
    vid = str(vacancy_id)
    direct: float | None = None
    if vid in affinity.positive_vacancy_ids:
        direct = 1.0
    elif vid in affinity.negative_vacancy_ids:
        direct = -1.0

    profile_score = max(0.0, min(1.0, float(base_score)))

    # Поведенческий blend (вычисляем всегда — нужен и для liked-вакансий,
    # чтобы liked-floor применялся уже к финальному сжатому значению).
    tau = affinity.trust
    beh = behavior_score_live(
        affinity,
        vacancy_category=vacancy_category,
        vacancy_specialization=vacancy_specialization,
        vacancy_skills=vacancy_skills or [],
        vacancy_title=vacancy_title or "",
    )
    blended = (1.0 - tau) * profile_score + tau * beh
    mult = multiplier_live(affinity, vacancy_skills or [], vacancy_title or "")
    raw = max(0.0, blended * mult)
    # ── Anti-saturation: см. ml-service/scoring.py::run_scoring ────────
    if raw <= 0.80:
        soft = raw
    else:
        over = raw - 0.80
        soft = 0.80 + 0.17 * math.tanh(over / 0.17)
    final = max(0.0, min(0.99, soft))

    # Прямой override применяется ПОСЛЕ anti-saturation, чтобы лайк
    # давал явный сигнал «выше всех остальных», но не убивал дисперсию.
    if direct is not None and direct >= POS_SENTIMENT_THRESHOLD:
        return min(0.99, max(final, DIRECT_POSITIVE_FLOOR)), 1.0, 1.0
    if direct is not None and direct <= NEG_SENTIMENT_THRESHOLD:
        capped = min(profile_score, DIRECT_NEGATIVE_CEILING)
        return round(capped * DIRECT_NEGATIVE_MULTIPLIER, 4), -1.0, -1.0

    # «Сила буста» в [-1, 1] для интерпретации в UI:
    #   = сдвиг финального скора относительно профиля, нормированный.
    boost_raw = final - profile_score
    boost = max(-1.0, min(1.0, boost_raw * 2.0))
    return final, boost, direct
