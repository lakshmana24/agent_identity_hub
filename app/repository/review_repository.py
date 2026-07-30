from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.models.review_report import ReviewReport

def create_review_report(db: Session, report_data: dict) -> ReviewReport:
    report = ReviewReport(**report_data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_review_reports(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[ReviewReport], int]:
    query = db.query(ReviewReport)
    total = query.count()
    reports = query.order_by(ReviewReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return reports, total

def find_stale_agents(db: Session, inactivity_days: int = 30) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=inactivity_days)

    active_agents = db.query(Agent).filter(Agent.lifecycle_status != "deprovisioned").all()
    stale_list: List[Dict[str, Any]] = []

    for agent in active_agents:
        # Find latest validation activity or action for this agent in audit_logs
        latest_audit = db.query(AuditLog).filter(
            AuditLog.agent_id == agent.id
        ).order_by(AuditLog.timestamp.desc()).first()

        if latest_audit and latest_audit.timestamp:
            last_activity = latest_audit.timestamp
        else:
            last_activity = agent.created_at

        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        days_inactive = (now - last_activity).days

        if last_activity <= threshold:
            # Flag agent for review
            if not agent.flagged_for_review:
                agent.flagged_for_review = True
                db.commit()

            stale_list.append({
                "agent_id": agent.id,
                "agent_name": agent.agent_name,
                "department": agent.department,
                "owner": agent.owner,
                "last_activity_at": last_activity,
                "days_inactive": days_inactive,
                "flagged_for_review": agent.flagged_for_review
            })

    return stale_list
