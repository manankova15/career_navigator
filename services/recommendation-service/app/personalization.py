"""
Personalization layer applied on top of the AHP content score.

Aggregates three local signal sources (no external data):
  1. UserLikedVacancy      — explicit heart icons in UI (sentiment +1).
  2. UserVacancySignal     — detail-page / bot 'interested / not interested'
                             buttons (sentiment −1 … +1).
  3. VacancyRecommendation.feedback of the latest session — 'positive'/'negative'/'saved'.

The final personalized score is

    S_final = clip( (S_base + Δ · τ · b_soft) · m_pattern ,  0 , 1 )

where
  Δ  = PERSONAL_SHIFT    — maximum additive shift (±);
  τ  = min(1, N/TRUST)   — credibility from interaction count;
  b_soft ∈ [−1, 1]       — smooth skill/title similarity to liked/disliked history;
  m_pattern              — multiplicative factor that STRONGLY demotes vacancies
                           dominated by disliked skills or title tokens, and
                           STRONGLY promotes vacancies that look like the liked
                           ones. Without `m_pattern` a high base score (0.89)
                           could never be toppled by the additive term alone.

If the user has already rated this exact vacancy (direct override), the soft
and multiplicative layers are skipped entirely.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from .models import UserLikedVacancy, UserVacancySignal, VacancyRecommendation

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-zа-яё0-9+#\.]+", re.I)
_STOPWORDS = {
    "и", "в", "на", "с", "для", "of", "the", "a", "an", "to", "in", "at",
    "по", "от", "или", "or", "and", "for", "into", "из",
}

# Soft additive shift.
PERSONAL_SHIFT = 0.50
TRUST_SATURATION = 3

# Multiplicative factor bounds — how far pattern match/penalty can reshape the score.
MULT_MIN = 0.20
MULT_MAX = 1.50
# Penalty coefficients — how strongly the skill / title pattern pulls the score down.
W_SKILL_PENALTY = 0.80
W_TITLE_PENALTY = 0.55
W_SKILL_REWARD = 0.35
W_TITLE_REWARD = 0.25
# Affinity threshold above which a skill is considered "liked" / below — "disliked".
POS_SKILL_THRESHOLD = 0.20
NEG_SKILL_THRESHOLD = -0.20

# Direct override on the exact vacancy the user has rated.
POSITIVE_FLOOR = 0.95
NEGATIVE_CEILING_MULTIPLIER = 0.10


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        m.group(0).lower()
        for m in _TOKEN_RE.finditer(text)
        if len(m.group(0)) > 1 and m.group(0).lower() not in _STOPWORDS
    }


@dataclass
class AffinityProfile:
    skill_weights: dict[str, float] = field(default_factory=dict)
    pos_title_tokens: set[str] = field(default_factory=set)
    neg_title_tokens: set[str] = field(default_factory=set)
    vacancy_sentiment: dict[str, float] = field(default_factory=dict)
    total_signals: int = 0

    @property
    def trust(self) -> float:
        """Credibility 0..1 — reaches 1.0 after TRUST_SATURATION signals."""
        if self.total_signals <= 0:
            return 0.0
        return min(1.0, self.total_signals / TRUST_SATURATION)

    def top_skills(self, n: int = 10) -> list[str]:
        return [
            s for s, _ in sorted(
                self.skill_weights.items(), key=lambda kv: kv[1], reverse=True
            )[:n]
            if self.skill_weights.get(s, 0) > 0
        ]

    def top_titles(self, n: int = 10) -> list[str]:
        return sorted(self.pos_title_tokens)[:n]


def _merge_signal(
    profile: AffinityProfile,
    raw_sum: dict[str, float],
    raw_cnt: dict[str, int],
    sentiment: float,
    skills: Iterable[str],
    title: str | None,
    vacancy_id: str | UUID,
) -> None:
    profile.total_signals += 1
    for s in skills or []:
        key = str(s).strip().lower()
        if not key:
            continue
        raw_sum[key] += sentiment
        raw_cnt[key] += 1
    toks = _tokens(title or "")
    if sentiment > 0:
        profile.pos_title_tokens.update(toks)
    elif sentiment < 0:
        profile.neg_title_tokens.update(toks)
    vid = str(vacancy_id)
    prev = profile.vacancy_sentiment.get(vid)
    if prev is None or abs(sentiment) >= abs(prev):
        profile.vacancy_sentiment[vid] = sentiment


def build_affinity(db: Session, user_id: UUID) -> AffinityProfile:
    """Collect every interaction the user ever gave and fold it into one profile."""
    raw_sum: dict[str, float] = defaultdict(float)
    raw_cnt: dict[str, int] = defaultdict(int)
    profile = AffinityProfile()

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
        _merge_signal(
            profile,
            raw_sum,
            raw_cnt,
            sentiment=1.0,
            skills=list(lv.vacancy_skills or []),
            title=lv.vacancy_title,
            vacancy_id=lv.vacancy_id,
        )

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
        _merge_signal(
            profile,
            raw_sum,
            raw_cnt,
            sentiment=float(sig.sentiment or 0.0),
            skills=list(sig.vacancy_skills or []),
            title=sig.vacancy_title,
            vacancy_id=sig.vacancy_id,
        )

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
    for rec in feedback_rows:
        if rec.feedback == "positive":
            s = 1.0
        elif rec.feedback == "negative":
            s = -1.0
        else:
            s = 0.0
        features = rec.features or {}
        _merge_signal(
            profile,
            raw_sum,
            raw_cnt,
            sentiment=s,
            skills=list(rec.matched_skills or []) + list(features.get("vacancy_skills") or []),
            title=features.get("vacancy_title"),
            vacancy_id=rec.vacancy_id,
        )

    for skill, total in raw_sum.items():
        n = raw_cnt.get(skill, 1)
        avg = total / n
        # Credibility shrinkage — a skill seen once pushed toward 0.
        shrunk = avg * n / (n + 1.0)
        profile.skill_weights[skill] = max(-1.0, min(1.0, shrunk))

    return profile


# ── Pattern-based multiplier ─────────────────────────────────────────────────

def _pattern_metrics(
    affinity: AffinityProfile,
    vacancy_skills: list[str],
    vacancy_title: str,
) -> dict[str, float]:
    skills = [str(s).strip().lower() for s in (vacancy_skills or []) if s]
    if skills:
        per = [affinity.skill_weights.get(s, 0.0) for s in skills]
        n = len(skills)
        neg_ratio = sum(1 for v in per if v <= NEG_SKILL_THRESHOLD) / n
        pos_ratio = sum(1 for v in per if v >= POS_SKILL_THRESHOLD) / n
    else:
        neg_ratio = pos_ratio = 0.0

    toks = _tokens(vacancy_title or "")
    if toks:
        neg_title = (
            len(toks & affinity.neg_title_tokens) / len(toks)
            if affinity.neg_title_tokens
            else 0.0
        )
        pos_title = (
            len(toks & affinity.pos_title_tokens) / len(toks)
            if affinity.pos_title_tokens
            else 0.0
        )
    else:
        neg_title = pos_title = 0.0

    return {
        "neg_skill_ratio": neg_ratio,
        "pos_skill_ratio": pos_ratio,
        "neg_title": neg_title,
        "pos_title": pos_title,
    }


def _soft_boost(metrics: dict[str, float]) -> float:
    skill_component = metrics["pos_skill_ratio"] - metrics["neg_skill_ratio"]
    title_component = metrics["pos_title"] - metrics["neg_title"]
    return max(-1.0, min(1.0, 0.70 * skill_component + 0.30 * title_component))


def _pattern_multiplier(metrics: dict[str, float], trust: float) -> float:
    penalty = (
        W_SKILL_PENALTY * metrics["neg_skill_ratio"]
        + W_TITLE_PENALTY * metrics["neg_title"]
    )
    reward = (
        W_SKILL_REWARD * metrics["pos_skill_ratio"]
        + W_TITLE_REWARD * metrics["pos_title"]
    )
    mult = 1.0 + trust * (reward - penalty)
    return max(MULT_MIN, min(MULT_MAX, mult))


# ── Public API ───────────────────────────────────────────────────────────────

def score_with_personalization(
    affinity: AffinityProfile,
    base_score: float,
    vacancy_id: str | UUID,
    vacancy_skills: list[str],
    vacancy_title: str,
) -> tuple[float, float, float | None]:
    """Return (final_score, soft_boost, direct_override)."""
    direct = affinity.vacancy_sentiment.get(str(vacancy_id))
    if direct is not None:
        if direct >= 0.999:
            return max(base_score, POSITIVE_FLOOR), 1.0, 1.0
        if direct <= -0.999:
            return round(base_score * NEGATIVE_CEILING_MULTIPLIER, 4), -1.0, -1.0

    metrics = _pattern_metrics(affinity, vacancy_skills or [], vacancy_title or "")
    boost = _soft_boost(metrics)
    tau = affinity.trust

    shifted = base_score + PERSONAL_SHIFT * tau * boost
    mult = _pattern_multiplier(metrics, tau)
    final = max(0.0, min(1.0, shifted * mult))
    return final, boost, direct
