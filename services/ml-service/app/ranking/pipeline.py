"""End-to-end hybrid ranking: LightGBM + content baseline blend."""

from __future__ import annotations

import logging
from typing import Any

import lightgbm as lgb
import numpy as np

from ..config import settings
from ..schemas import RankRequest, RankResponse, RankedVacancy, ScoredVacancy
from .feature_extractor import FeatureExtractor, minmax_norm

logger = logging.getLogger(__name__)


def _vacancy_to_dict(v: Any) -> dict[str, Any]:
    if hasattr(v, "model_dump"):
        return v.model_dump(mode="json")
    return dict(v)


def _profile_to_dict(p: Any) -> dict[str, Any]:
    if hasattr(p, "model_dump"):
        return p.model_dump(mode="json")
    return dict(p)


def run_hybrid_rank(request: RankRequest, booster: lgb.Booster | None) -> RankResponse:
    extractor = FeatureExtractor()
    profile_dict = _profile_to_dict(request.profile)
    vacancies_dicts = [_vacancy_to_dict(v) for v in request.vacancies]

    content_by_id: dict[str, ScoredVacancy] = {str(r.vacancy_id): r for r in request.content_results}
    content_scores = {str(r.vacancy_id): float(r.score) for r in request.content_results}

    user_stats = request.user_stats or {}
    vac_stats = request.vacancy_stats or {}
    vac_stats_merged: dict[str, dict[str, Any]] = {str(k): dict(v) for k, v in vac_stats.items()}

    X = extractor.build_matrix(
        profile_dict,
        vacancies_dicts,
        content_scores,
        user_stats={k: float(v) for k, v in user_stats.items()},
        vacancy_stats_by_id=vac_stats_merged,
    )

    n = len(request.vacancies)
    used_ml = False
    pred_norm = np.zeros(n, dtype=np.float64)

    if booster is not None and X.shape[0] == n and n > 0:
        try:
            pred = booster.predict(X)
            pred_norm = minmax_norm(np.array(pred, dtype=np.float64))
            used_ml = True
        except Exception as exc:
            logger.warning("ML predict failed, using content scores: %s", exc)
            pred_norm = np.array([content_scores[str(v.vacancy_id)] for v in request.vacancies], dtype=np.float64)
    else:
        pred_norm = np.array([content_scores.get(str(v.vacancy_id), 0.0) for v in request.vacancies], dtype=np.float64)

    content_arr = np.array([content_scores[str(v.vacancy_id)] for v in request.vacancies], dtype=np.float64)
    w_ml = float(settings.blend_ml_weight)
    w_ct = float(settings.blend_content_weight)
    s = w_ml + w_ct
    if s > 0:
        w_ml, w_ct = w_ml / s, w_ct / s
    final = w_ml * pred_norm + w_ct * content_arr

    order = np.argsort(-final)
    ranked: list[RankedVacancy] = []
    for idx in order:
        i = int(idx)
        vac = request.vacancies[i]
        vid = str(vac.vacancy_id)
        base = content_by_id.get(vid)
        if not base:
            continue
        expl = [
            f"ML-ранг: {pred_norm[i]:.2f}" if used_ml else "ML-модель недоступна, используется базовый скор",
            f"Контентный скор: {base.score:.2f}",
        ]
        ranked.append(
            RankedVacancy(
                vacancy_id=base.vacancy_id,
                score=round(float(final[i]), 4),
                skill_score=base.skill_score,
                location_score=base.location_score,
                salary_score=base.salary_score,
                seniority_score=base.seniority_score,
                matched_skills=base.matched_skills,
                missing_skills=base.missing_skills,
                reasons=list(base.reasons),
                ml_score=round(float(pred_norm[i]), 4),
                content_score=round(float(base.score), 4),
                rank_explanation=expl,
            )
        )

    return RankResponse(
        user_id=request.profile.user_id,
        algorithm="hybrid_lgb_v1",
        total_ranked=len(ranked),
        results=ranked,
        used_ml_model=used_ml,
    )
