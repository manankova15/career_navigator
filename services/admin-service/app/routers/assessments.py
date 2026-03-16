from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..crud import log_action
from ..database import get_db
from ..proxy import get_assessments, publish_assessment
from ..schemas import AdminActionResult, AssessmentPublish
from ..security import get_actor_id, require_admin

router = APIRouter(prefix="/admin/assessments", tags=["admin-assessments"])


@router.get("")
async def list_assessments_admin(
    _admin_id: UUID = Depends(get_actor_id),
):
    """List all assessments including drafts."""
    try:
        return await get_assessments()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.patch("/{assessment_id}/publish", response_model=AdminActionResult)
async def toggle_publish(
    assessment_id: UUID,
    payload: AssessmentPublish,
    request: Request,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(require_admin),
    actor_id: UUID = Depends(get_actor_id),
):
    """Publish or unpublish an assessment."""
    try:
        await publish_assessment(str(assessment_id), payload.is_published)
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
