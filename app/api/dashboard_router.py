from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.schemas.dashboard_schemas import DashboardMetricsResponse
from app.services.dashboard_service import get_dashboard_service
from app.models.admin import Admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])

@router.get("", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return get_dashboard_service(db)
