from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def create_audit_log(db: Session, audit_data: dict) -> AuditLog:
    log = AuditLog(**audit_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_audit_logs(
    db: Session,
    agent_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    performed_by: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[AuditLog], int]:
    query = db.query(AuditLog)

    if agent_id:
        query = query.filter(AuditLog.agent_id == agent_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AuditLog.timestamp <= date_to)
    if performed_by:
        query = query.filter(AuditLog.performed_by.ilike(f"%{performed_by}%"))

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return logs, total
