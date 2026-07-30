from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.schemas.review_schemas import ReviewReportListResponse, ReviewReportResponse, StaleAgentResponse
from app.repository.review_repository import find_stale_agents, get_review_reports, generate_team_quarterly_report
from app.scheduler.jobs import (
    check_expired_credentials_job,
    detect_stale_agents_job,
    generate_governance_reviews_job
)
from app.models.admin import Admin

router = APIRouter(prefix="/reviews", tags=["Governance Reviews & Stale Agent Reports"])

@router.get("/stale-agents", response_model=List[StaleAgentResponse])
def get_stale_agents(
    inactivity_days: int = Query(30, ge=0, description="Inactivity threshold in days (default 30 days)"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    stale_data = find_stale_agents(db, inactivity_days=inactivity_days)
    return [StaleAgentResponse.model_validate(item) for item in stale_data]

@router.get("/report")
def get_quarterly_review_report(
    owning_team: Optional[str] = Query(None, description="Filter report by owning team (e.g. Growth, Finance, DevOps)"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return generate_team_quarterly_report(db, owning_team=owning_team)

@router.get("", response_model=ReviewReportListResponse)
def list_review_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    reports, total = get_review_reports(db, page=page, page_size=page_size)
    response_reports = [ReviewReportResponse.model_validate(r) for r in reports]
    return ReviewReportListResponse(
        total=total,
        page=page,
        page_size=page_size,
        reports=response_reports
    )

@router.post("/run")
def trigger_manual_governance_jobs(
    current_admin: Admin = Depends(get_current_admin)
):
    check_expired_credentials_job()
    detect_stale_agents_job()
    generate_governance_reviews_job()
    return {"status": "success", "message": "Manual execution of background governance jobs completed."}
