"""История запусков ingestion (таблица ingestion_runs) и параметры расписания.

Доступ только под админом — admin-service проксирует запросы сюда.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import IngestionRun, SystemSetting
from ..schemas import (
    IngestionRunOut,
    IngestionRunsPage,
    IngestionScheduleOut,
    IngestionScheduleUpdate,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


_SCHEDULE_KEY = "ingestion_schedule"
_DEFAULTS = {
    "fetch_interval_hours": 2,
    "normalize_interval_minutes": 30,
}


def _load_schedule(db: Session) -> dict:
    row = db.query(SystemSetting).filter(SystemSetting.key == _SCHEDULE_KEY).first()
    value = dict(_DEFAULTS)
    if row and isinstance(row.value, dict):
        value.update({k: v for k, v in row.value.items() if k in _DEFAULTS})
    return value


# ── Runs ──────────────────────────────────────────────────────────────────────


@router.get("/runs", response_model=IngestionRunsPage)
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    q = db.query(IngestionRun)
    if source_id is not None:
        q = q.filter(IngestionRun.source_id == source_id)
    if status_filter:
        q = q.filter(IngestionRun.status == status_filter)
    total = q.count()
    items = (
        q.order_by(IngestionRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return IngestionRunsPage(
        items=[IngestionRunOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    row = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    db.delete(row)
    db.commit()


# ── Schedule ──────────────────────────────────────────────────────────────────


@router.get("/schedule", response_model=IngestionScheduleOut)
def get_schedule(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    value = _load_schedule(db)
    return IngestionScheduleOut(**value)


@router.patch("/schedule", response_model=IngestionScheduleOut)
def update_schedule(
    payload: IngestionScheduleUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    row = db.query(SystemSetting).filter(SystemSetting.key == _SCHEDULE_KEY).first()
    current = _load_schedule(db)
    update_dict = payload.model_dump(exclude_none=True)
    current.update(update_dict)
    if row is None:
        row = SystemSetting(key=_SCHEDULE_KEY, value=current)
        db.add(row)
    else:
        row.value = current
    db.commit()
    return IngestionScheduleOut(**current)
