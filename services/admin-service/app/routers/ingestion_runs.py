"""Admin proxy: история запусков дозагрузки + расписание."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import (
    delete_ingestion_run,
    get_ingestion_runs,
    get_ingestion_schedule,
    update_ingestion_schedule,
)
from ..security import get_actor_id, get_forward_authorization, require_admin

router = APIRouter(prefix="/admin/ingestion", tags=["admin-ingestion"])


@router.get("/runs")
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    try:
        return await get_ingestion_runs(
            authorization,
            page=page,
            page_size=page_size,
            source_id=source_id,
            status_filter=status_filter,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        code = await delete_ingestion_run(authorization, str(run_id))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if code >= 400:
        raise HTTPException(status_code=code, detail="Failed to delete run")
    log_action(
        db,
        actor_user_id=actor_id,
        action="ingestion_run.deleted",
        resource_type="ingestion_run",
        resource_id=str(run_id),
        details={},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )


@router.get("/schedule")
async def get_schedule(
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    try:
        return await get_ingestion_schedule(authorization)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.patch("/schedule")
async def patch_schedule(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        result = await update_ingestion_schedule(authorization, payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    log_action(
        db,
        actor_user_id=actor_id,
        action="ingestion_schedule.updated",
        resource_type="ingestion_schedule",
        resource_id="global",
        details=payload,
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return result
