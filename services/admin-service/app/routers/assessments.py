from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import (
    add_assessment_item,
    create_assessment,
    delete_assessment,
    delete_assessment_item,
    get_assessment_admin,
    get_assessments,
    publish_assessment,
    update_assessment,
    update_assessment_item,
)
from ..schemas import AdminActionResult, AssessmentPublish
from ..security import get_actor_id, get_forward_authorization, require_admin

router = APIRouter(prefix="/admin/assessments", tags=["admin-assessments"])


@router.get("")
async def list_assessments_admin(
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """List all assessments including drafts."""
    try:
        return await get_assessments(authorization)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/{assessment_id}")
async def get_assessment_full(
    assessment_id: UUID,
    authorization: str = Depends(get_forward_authorization),
    _admin_id: UUID = Depends(get_actor_id),
):
    """Get a single assessment with full item data (admin)."""
    try:
        return await get_assessment_admin(authorization, str(assessment_id))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_assessment_proxy(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Create a new assessment (proxied to assessment-service)."""
    try:
        result = await create_assessment(authorization, payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.created",
        resource_type="assessment",
        resource_id=str(result.get("id", "")),
        details={"title": payload.get("title")},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.patch("/{assessment_id}")
async def update_assessment_proxy(
    assessment_id: UUID,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Update assessment fields."""
    try:
        result = await update_assessment(authorization, str(assessment_id), payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.updated",
        resource_type="assessment",
        resource_id=str(assessment_id),
        details=payload,
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment_proxy(
    assessment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        code = await delete_assessment(authorization, str(assessment_id))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if code >= 400:
        raise HTTPException(status_code=code, detail="Failed to delete assessment")
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.deleted",
        resource_type="assessment",
        resource_id=str(assessment_id),
        details={},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )


@router.patch("/{assessment_id}/publish", response_model=AdminActionResult)
async def toggle_publish(
    assessment_id: UUID,
    payload: AssessmentPublish,
    request: Request,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
    authorization: str = Depends(get_forward_authorization),
):
    """Publish or unpublish an assessment."""
    try:
        await publish_assessment(
            authorization, str(assessment_id), payload.is_published
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    action = "assessment.published" if payload.is_published else "assessment.unpublished"
    log_action(
        db,
        actor_user_id=actor_id,
        action=action,
        resource_type="assessment",
        resource_id=str(assessment_id),
        details={"is_published": payload.is_published},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    verb = "published" if payload.is_published else "unpublished"
    return AdminActionResult(success=True, message=f"Assessment {assessment_id} {verb}")


# ── Items ────────────────────────────────────────────────────────────────────


@router.post("/{assessment_id}/items", status_code=status.HTTP_201_CREATED)
async def add_item_proxy(
    assessment_id: UUID,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        result = await add_assessment_item(authorization, str(assessment_id), payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.item.created",
        resource_type="assessment_item",
        resource_id=str(result.get("id", "")),
        details={"assessment_id": str(assessment_id)},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.patch("/items/{item_id}")
async def patch_item_proxy(
    item_id: UUID,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        result = await update_assessment_item(authorization, str(item_id), payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.item.updated",
        resource_type="assessment_item",
        resource_id=str(item_id),
        details={},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_proxy(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Depends(get_forward_authorization),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    try:
        code = await delete_assessment_item(authorization, str(item_id))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if code >= 400:
        raise HTTPException(status_code=code, detail="Failed to delete item")
    log_action(
        db,
        actor_user_id=actor_id,
        action="assessment.item.deleted",
        resource_type="assessment_item",
        resource_id=str(item_id),
        details={},
        actor_email=admin_payload.get("email"),
        ip_address=request.client.host if request.client else None,
    )
