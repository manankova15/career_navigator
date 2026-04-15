from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_sources, trigger_source_sync
from ..schemas import AdminActionResult, SourceSyncTriggerIn, SyncTriggerResult
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
    """Manually trigger ingestion sync for a source."""
    sync_body: dict = {}
    if payload.max_vacancies is not None:
        sync_body["max_vacancies"] = payload.max_vacancies
    try:
        await trigger_source_sync(authorization, str(source_id), body=sync_body)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    log_action(
        db,
        actor_user_id=actor_id,
        action="source.sync_triggered",
        resource_type="source",
        resource_id=str(source_id),
        details={"max_vacancies": payload.max_vacancies},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    msg = "Sync job enqueued"
    if payload.max_vacancies is not None:
        msg += f" (max_vacancies={payload.max_vacancies})"
    return SyncTriggerResult(
        source_id=str(source_id),
        status="triggered",
        message=msg,
    )
