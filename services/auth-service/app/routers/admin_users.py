from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..crud import count_all_users, get_user_primary_email, get_user_roles, list_users_admin
from ..database import get_db
from ..deps import require_admin
from ..schemas import AdminStatsOut, AdminUserListItem, AdminUserListPage

router = APIRouter(prefix="/auth/admin", tags=["auth-admin"])


@router.get("/users", response_model=AdminUserListPage)
def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _payload: dict = Depends(require_admin),
):
    offset = (page - 1) * page_size
    users, total = list_users_admin(db, offset=offset, limit=page_size)
    items = [
        AdminUserListItem(
            user_id=u.id,
            full_name=u.full_name,
            email=get_user_primary_email(db, u.id),
            roles=get_user_roles(db, u.id),
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]
    return AdminUserListPage(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(
    db: Session = Depends(get_db),
    _payload: dict = Depends(require_admin),
):
    return AdminStatsOut(total_users=count_all_users(db))
