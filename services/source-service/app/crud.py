from uuid import UUID

from sqlalchemy.orm import Session

from .models import VacancySource
from .schemas import SourceIn


def list_sources(db: Session, enabled_only: bool = False) -> list[VacancySource]:
    q = db.query(VacancySource)
    if enabled_only:
        q = q.filter(VacancySource.enabled == True)  # noqa: E712
    return q.order_by(VacancySource.name).all()


def get_source(db: Session, source_id: UUID) -> VacancySource | None:
    return db.query(VacancySource).filter(VacancySource.id == source_id).first()


def create_source(db: Session, data: SourceIn) -> VacancySource:
    source = VacancySource(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_source(db: Session, source_id: UUID, data: SourceIn) -> VacancySource | None:
    source = get_source(db, source_id)
    if not source:
        return None
    for key, value in data.model_dump().items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


def toggle_source(db: Session, source_id: UUID, enabled: bool) -> VacancySource | None:
    source = get_source(db, source_id)
    if not source:
        return None
    source.enabled = enabled
    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, source_id: UUID) -> bool:
    source = get_source(db, source_id)
    if not source:
        return False
    db.delete(source)
    db.commit()
    return True
