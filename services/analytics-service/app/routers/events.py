from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..crud import ingest_event, upsert_assessment_stat
from ..database import get_db
from ..schemas import AssessmentEventIn, EventIn
from ..security import require_internal_or_service

router = APIRouter(prefix="/analytics/events", tags=["events"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def ingest(
    payload: EventIn,
    db: Session = Depends(get_db),
    _=Depends(require_internal_or_service),
):
    """Ingest a domain event from any other service."""
    ingest_event(db, payload.user_id, payload.event_type, payload.resource_type,
                 payload.resource_id, payload.properties, payload.occurred_at)
    return {"status": "accepted"}


@router.post("/assessment-completed", status_code=status.HTTP_202_ACCEPTED)
def ingest_assessment(
    payload: AssessmentEventIn,
    db: Session = Depends(get_db),
    _=Depends(require_internal_or_service),
):
    """Convenience endpoint for assessment_completed events with stats update."""
    ingest_event(db, payload.user_id, "assessment_completed",
                 "assessment", str(payload.assessment_id), {"percentage": payload.percentage})
    upsert_assessment_stat(db, payload.user_id, payload.assessment_id,
                           payload.topic, payload.percentage)
    return {"status": "accepted"}
