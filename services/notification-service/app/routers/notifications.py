from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import (
    create_notification,
    get_delivery_stats,
    get_notification,
    list_user_notifications,
    mark_all_read,
    mark_read,
    retry_failed,
)
from ..database import get_db
from ..dispatcher import dispatch_notification
from ..schemas import (
    BulkDispatchRequest,
    BulkDispatchResult,
    DeliveryStats,
    DispatchRequest,
    DispatchResult,
    NotificationOut,
    NotificationPage,
    NotificationSummaryOut,
)
from ..security import get_current_user_id, require_admin, require_internal_or_admin
from ..templates import SUPPORTED_TEMPLATES

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Dispatch (internal + admin) ───────────────────────────────────────────────

@router.post("/dispatch", response_model=DispatchResult, status_code=status.HTTP_202_ACCEPTED)
async def dispatch(
    payload: DispatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _caller=Depends(require_internal_or_admin),
):
    """
    Create and dispatch a notification.
    Accepted by other services via X-Internal-Token header
    or by admins via Bearer JWT.
    Response is returned immediately; actual send happens in background.
    """
    notification = create_notification(
        db,
        user_id=payload.user_id,
        channel=payload.channel,
        template_name=payload.template_name,
        context=payload.context,
    )
    background_tasks.add_task(
        dispatch_notification,
        db=db,
        notification_id=notification.id,
        user_email=payload.to_email,
    )
    return DispatchResult(
        notification_id=notification.id,
        channel=payload.channel,
        status="queued",
    )


@router.post(
    "/dispatch/bulk",
    response_model=BulkDispatchResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_bulk(
    payload: BulkDispatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _caller=Depends(require_internal_or_admin),
):
    """Dispatch the same template+context to a list of users."""
    ids: list[UUID] = []
    for user_id in payload.user_ids:
        notif = create_notification(
            db,
            user_id=user_id,
            channel=payload.channel,
            template_name=payload.template_name,
            context=payload.context,
        )
        background_tasks.add_task(
            dispatch_notification,
            db=db,
            notification_id=notif.id,
            user_email=None,
        )
        ids.append(notif.id)
    return BulkDispatchResult(queued=len(ids), notification_ids=ids)


# ── User inbox ────────────────────────────────────────────────────────────────

@router.get("/me", response_model=NotificationPage)
def my_notifications(
    unread_only: bool = Query(False),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return paginated notification inbox for the authenticated user."""
    offset = (page - 1) * page_size
    items, total, unread = list_user_notifications(
        db,
        user_id,
        unread_only=unread_only,
        channel=channel,
        offset=offset,
        limit=page_size,
    )
    return NotificationPage(
        items=[NotificationSummaryOut.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
        page=page,
        page_size=page_size,
    )


@router.get("/me/{notification_id}", response_model=NotificationOut)
def get_my_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return full notification detail including delivery status."""
    notif = get_notification(db, notification_id)
    if not notif or notif.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notif


@router.patch("/me/{notification_id}/read", response_model=NotificationSummaryOut)
def read_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark a single notification as read."""
    notif = mark_read(db, notification_id, user_id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notif


@router.post("/me/read-all")
def read_all_notifications(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark all unread notifications as read."""
    count = mark_all_read(db, user_id)
    return {"marked_read": count}


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/stats", response_model=DeliveryStats)
def delivery_stats(
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: overall delivery statistics."""
    return DeliveryStats(**get_delivery_stats(db))


@router.post("/admin/retry/{notification_id}", status_code=status.HTTP_202_ACCEPTED)
async def retry_notification(
    notification_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: retry a failed notification delivery."""
    delivery = retry_failed(db, notification_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No failed delivery found for this notification",
        )
    background_tasks.add_task(
        dispatch_notification,
        db=db,
        notification_id=notification_id,
        user_email=None,
    )
    return {"notification_id": str(notification_id), "status": "retry_queued"}


# ── Meta ──────────────────────────────────────────────────────────────────────

@router.get("/templates", tags=["meta"])
def list_templates():
    """List all available notification templates."""
    return {"templates": SUPPORTED_TEMPLATES}
