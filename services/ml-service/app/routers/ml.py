from pathlib import Path

from fastapi import APIRouter, Depends, Request

from ..config import settings
from ..ranking.model_loader import load_ranker
from ..ranking.pipeline import run_hybrid_rank
from ..schemas import (
    RankRequest,
    RankResponse,
    ScoreRequest,
    ScoreResponse,
    SkillGapRequest,
    SkillGapResponse,
)
from ..scoring import run_scoring
from ..security import require_internal
from ..skillgap import compute_skill_gap
from ..training.trainer import train_and_save

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score vacancies for a user profile (Phase 1 content-based)",
)
async def score_vacancies(
    request: ScoreRequest,
    _: None = Depends(require_internal),
):
    return run_scoring(request)


@router.post(
    "/skill-gap",
    response_model=SkillGapResponse,
    summary="Compute skill gaps against target vacancies",
)
async def skill_gap(
    request: SkillGapRequest,
    _: None = Depends(require_internal),
):
    return compute_skill_gap(request)


@router.post(
    "/rank",
    response_model=RankResponse,
    summary="Hybrid LightGBM re-ranking on top of content scores",
)
async def rank_vacancies(
    body: RankRequest,
    req: Request,
    _: None = Depends(require_internal),
):
    booster = getattr(req.app.state, "rank_booster", None)
    return run_hybrid_rank(body, booster)


@router.post(
    "/train",
    summary="Retrain ranker (internal). Replaces model on disk and reloads booster.",
)
async def train_ranker(
    req: Request,
    _: None = Depends(require_internal),
):
    root = Path(settings.model_dir)
    train_and_save(root)
    booster = load_ranker(root)
    req.app.state.rank_booster = booster
    return {"status": "ok", "model_dir": str(root)}
