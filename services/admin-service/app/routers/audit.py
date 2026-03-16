from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..crud import list_audit_logs
from ..database import get_db
from ..schemas import AuditLogOut, AuditLogPage
from ..security import get_actor_id

router = APIRouter(prefix="/admin/audit", tags=["audit"])


@router.get("", response_model=AuditLogPage)
def get_audit_logs(
    actor_user_id: UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(get_actor_id),
):
    offset = (page - 1) * page_size
    items, total = list_audit_logs(
        db,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        offset=offset,
        limit=page_size,
    )
    return AuditLogPage(items=items, total=total, page=page, page_size=page_size)
