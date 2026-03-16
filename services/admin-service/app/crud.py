from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from .models import AdminAuditLog


def log_action(
    db: Session,
    actor_user_id: UUID,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    actor_email: str | None = None,
    ip_address: str | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(
    db: Session,
    actor_user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[AdminAuditLog], int]:
    q = db.query(AdminAuditLog)
    if actor_user_id:
        q = q.filter(AdminAuditLog.actor_user_id == actor_user_id)
    if action:
        q = q.filter(AdminAuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        q = q.filter(AdminAuditLog.resource_type == resource_type)
    total = q.count()
    items = q.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return items, total
