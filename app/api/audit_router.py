from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.schemas.audit_schemas import AuditLogListResponse, AuditLogResponse
from app.repository.audit_repository import get_audit_logs
from app.models.admin import Admin

router = APIRouter(prefix="/audit", tags=["Audit Logging"])

@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    agent_id: Optional[str] = Query(None, description="Filter by Agent ID"),
    action: Optional[str] = Query(None, description="Filter by action name (e.g., agent.register, credential.validate)"),
    date_from: Optional[datetime] = Query(None, description="Filter logs starting from datetime (UTC)"),
    date_to: Optional[datetime] = Query(None, description="Filter logs up to datetime (UTC)"),
    performed_by: Optional[str] = Query(None, description="Filter by performing user or agent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    logs, total = get_audit_logs(
        db,
        agent_id=agent_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        performed_by=performed_by,
        page=page,
        page_size=page_size
    )
    audit_responses = [AuditLogResponse.model_validate(l) for l in logs]
    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        logs=audit_responses
    )
