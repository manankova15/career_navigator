from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..crud import (
    count_user_events_by_type,
    get_dau_series,
    get_product_metrics,
    get_user_assessment_stats,
)
from ..database import get_db
from ..schemas import AssessmentStatOut, DashboardOut, DauPoint, ProductMetricsOut, UserProgressOut
from ..security import get_current_user_id, require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me/progress", response_model=UserProgressOut)
def my_progress(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return the authenticated user's assessment progress and activity summary."""
    stats = get_user_assessment_stats(db, user_id)
    vacancy_views = count_user_events_by_type(db, user_id, "vacancy_viewed")
    rec_clicks = count_user_events_by_type(db, user_id, "recommendation_clicked")
    best = max((s.best_percentage for s in stats), default=0.0)
    avg = round(sum(s.avg_percentage for s in stats) / len(stats), 2) if stats else 0.0
    total_attempts = sum(s.attempts_count for s in stats)
    return UserProgressOut(
        user_id=user_id,
        total_attempts=total_attempts,
        avg_score=avg,
        best_score=best,
        assessments_taken=len(stats),
        vacancy_views=vacancy_views,
        recommendation_clicks=rec_clicks,
        recent_stats=[AssessmentStatOut.model_validate(s) for s in stats[:10]],
    )


@router.get("/admin/dashboard", response_model=DashboardOut)
def admin_dashboard(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: product-level dashboard with DAU series."""
    metrics = get_product_metrics(db)
    dau = get_dau_series(db, days=days)
    return DashboardOut(
        metrics=ProductMetricsOut(**metrics),
        dau_series=[DauPoint(**d) for d in dau],
    )


@router.get("/admin/metrics", response_model=ProductMetricsOut)
def product_metrics(
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    return ProductMetricsOut(**get_product_metrics(db))
