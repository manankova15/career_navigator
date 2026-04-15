from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import (
    create_source,
    delete_source,
    get_source,
    list_sources,
    toggle_source,
    update_source,
)
from ..database import get_db
from ..deps import require_admin
from ..ingestion_tasks import enqueue_fetch_source
from ..schemas import SourceIn, SourceOut, SourceSyncIn, SourceToggle

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def get_sources(
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return list_sources(db, enabled_only=enabled_only)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source_by_id(source_id: UUID, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.post("/{source_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion_sync(
    source_id: UUID,
    body: SourceSyncIn = Body(default_factory=SourceSyncIn),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    """Поставить в очередь Celery задачу дозагрузки вакансий для источника."""
    source = get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if not source.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source is disabled; enable it before syncing",
        )
    max_v = body.max_vacancies
    try:
        enqueue_fetch_source(str(source_id), max_vacancies=max_v)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not enqueue sync: {exc}",
        ) from exc
    return {
        "source_id": str(source_id),
        "status": "queued",
        "max_vacancies": max_v,
    }


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_new_source(
    data: SourceIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    return create_source(db, data)


@router.put("/{source_id}", response_model=SourceOut)
async def update_existing_source(
    source_id: UUID,
    data: SourceIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    source = update_source(db, source_id, data)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.patch("/{source_id}/toggle", response_model=SourceOut)
async def toggle_source_enabled(
    source_id: UUID,
    data: SourceToggle,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    source = toggle_source(db, source_id, data.enabled)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_source(
    source_id: UUID,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    if not delete_source(db, source_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
