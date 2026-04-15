from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..proxy import get_assessment_admin_stats, get_auth_admin_stats
from ..schemas import AdminDashboardStatsOut
from ..security import get_actor_id, get_forward_authorization

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])


@router.get("", response_model=AdminDashboardStatsOut)
async def combined_dashboard_stats(
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """Сводка: пользователи из auth-service, завершённые тесты из assessment-service."""
    try:
        auth_data = await get_auth_admin_stats(authorization)
        as_data = await get_assessment_admin_stats(authorization)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return AdminDashboardStatsOut(
        total_users=int(auth_data.get("total_users", 0)),
        completed_attempts=int(as_data.get("completed_attempts", 0)),
        users_with_completed_attempts=int(
            as_data.get("users_with_completed_attempts", 0)
        ),
    )
