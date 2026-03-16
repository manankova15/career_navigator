from fastapi import APIRouter, Depends

from ..schemas import ScoreRequest, ScoreResponse, SkillGapRequest, SkillGapResponse
from ..scoring import run_scoring
from ..security import require_internal
from ..skillgap import compute_skill_gap

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
