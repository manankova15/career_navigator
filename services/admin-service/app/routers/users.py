from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_users
from ..schemas import AdminActionResult
from ..security import get_actor_id, get_forward_authorization, require_admin

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("")
async def list_users(
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """List all registered users."""
    try:
        return await get_users(authorization)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/{user_id}/notify", response_model=AdminActionResult)
async def send_admin_notification(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Dispatch a system notification to a specific user (in-app)."""
    import httpx
    from ..config import settings
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.notification_service_url}/notifications/dispatch",
                headers={"X-Internal-Token": settings.internal_token},
                json={
                    "user_id": str(user_id),
                    "channel": "in-app",
                    "template_name": "welcome",
                    "context": {"name": "User"},
                },
            )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    log_action(
        db,
        actor_user_id=actor_id,
        action="user.notification_sent",
        resource_type="user",
        resource_id=str(user_id),
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return AdminActionResult(success=True, message=f"Notification dispatched to {user_id}")
