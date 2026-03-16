from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_sources, trigger_source_sync
from ..schemas import AdminActionResult, SyncTriggerResult
from ..security import get_actor_id, require_admin

router = APIRouter(prefix="/admin/sources", tags=["admin-sources"])


@router.get("")
async def list_sources(
    _admin_id: UUID = Depends(get_actor_id),
):
    """List all vacancy sources."""
    try:
        return await get_sources()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/{source_id}/sync", response_model=SyncTriggerResult)
async def trigger_sync(
    source_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Manually trigger ingestion sync for a source."""
    try:
        await trigger_source_sync(str(source_id))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    log_action(
        db,
        actor_user_id=actor_id,
        action="source.sync_triggered",
        resource_type="source",
        resource_id=str(source_id),
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return SyncTriggerResult(
        source_id=str(source_id),
        status="triggered",
        message="Sync job enqueued",
    )
