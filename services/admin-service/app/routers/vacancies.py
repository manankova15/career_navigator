from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_vacancies, moderate_vacancy
from ..schemas import AdminActionResult, VacancyModerate
from ..security import get_actor_id, require_admin

router = APIRouter(prefix="/admin/vacancies", tags=["admin-vacancies"])


@router.get("")
async def list_vacancies_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    _admin_id: UUID = Depends(get_actor_id),
):
    """Proxy: list all vacancies (including non-active) for admin review."""
    try:
        return await get_vacancies(page=page, page_size=page_size, q=q)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.patch("/{vacancy_id}/status", response_model=AdminActionResult)
async def moderate_vacancy_status(
    vacancy_id: UUID,
    payload: VacancyModerate,
    request: Request,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Set vacancy status (active | archived | blocked)."""
    try:
        await moderate_vacancy(str(vacancy_id), payload.status)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    log_action(
        db,
        actor_user_id=actor_id,
        action="vacancy.moderate",
        resource_type="vacancy",
        resource_id=str(vacancy_id),
        details={"new_status": payload.status},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return AdminActionResult(
        success=True, message=f"Vacancy {vacancy_id} status set to {payload.status}"
    )
