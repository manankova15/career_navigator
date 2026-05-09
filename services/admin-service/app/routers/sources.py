from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_source_sync_job, get_sources, trigger_source_sync
from ..schemas import (
    AdminActionResult,
    SourceSyncTriggerIn,
    SyncJobStatusOut,
    SyncTriggerResult,
)
from ..security import get_actor_id, get_forward_authorization, require_admin

router = APIRouter(prefix="/admin/sources", tags=["admin-sources"])


@router.get("")
async def list_sources(
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """List all vacancy sources."""
    try:
        return await get_sources(authorization)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/{source_id}/sync", response_model=SyncTriggerResult)
async def trigger_sync(
    source_id: UUID,
    request: Request,
    payload: SourceSyncTriggerIn = Body(default_factory=SourceSyncTriggerIn),
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
    authorization: str = Depends(get_forward_authorization),
):
    """Manually trigger ingestion sync for a source.

    Возвращает task_id — фронт использует его для опроса статуса через
    GET /admin/sources/sync/jobs/{task_id}.
    """
    sync_body: dict = {}
    if payload.max_vacancies is not None:
        sync_body["max_vacancies"] = payload.max_vacancies
    try:
        downstream = await trigger_source_sync(authorization, str(source_id), body=sync_body)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    task_id: str | None = None
    if isinstance(downstream, dict):
        raw_task_id = downstream.get("task_id")
        if isinstance(raw_task_id, str) and raw_task_id:
            task_id = raw_task_id

    log_action(
        db,
        actor_user_id=actor_id,
        action="source.sync_triggered",
        resource_type="source",
        resource_id=str(source_id),
        details={"max_vacancies": payload.max_vacancies, "task_id": task_id},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    msg = "Sync job enqueued"
    if payload.max_vacancies is not None:
        msg += f" (max_vacancies={payload.max_vacancies})"
    if task_id:
        msg += f" [task_id={task_id}]"
    return SyncTriggerResult(
        source_id=str(source_id),
        status="triggered",
        message=msg,
        task_id=task_id,
        max_vacancies=payload.max_vacancies,
    )


@router.get("/sync/jobs/{task_id}", response_model=SyncJobStatusOut)
async def sync_job_status(
    task_id: str,
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """Прокси-чтение состояния задачи дозагрузки (Celery) по task_id."""
    try:
        data = await get_source_sync_job(authorization, task_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected sync job status payload",
        )
    return SyncJobStatusOut(**data)
