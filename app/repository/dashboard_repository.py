from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.credential import Credential
from app.models.audit_log import AuditLog

def get_dashboard_metrics_data(db: Session) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    near_expiry_threshold = now + timedelta(days=7)

    # 1. Total agents (excluding deprovisioned)
    total_agents = db.query(func.count(Agent.id)).filter(Agent.lifecycle_status != "deprovisioned").scalar() or 0

    # 2. Active agents
    active_agents = db.query(func.count(Agent.id)).filter(Agent.lifecycle_status == "active").scalar() or 0

    # 3. Suspended agents
    suspended_agents = db.query(func.count(Agent.id)).filter(Agent.lifecycle_status == "suspended").scalar() or 0

    # 4. Expired credentials (inactive or past expires_at)
    expired_credentials = db.query(func.count(Credential.id)).filter(
        or_(Credential.active == False, Credential.expires_at < now)
    ).scalar() or 0

    # 5. Credentials near expiry (active and expires in next 7 days)
    credentials_near_expiry = db.query(func.count(Credential.id)).filter(
        Credential.active == True,
        Credential.expires_at >= now,
        Credential.expires_at <= near_expiry_threshold
    ).scalar() or 0

    # 6. Pending reviews (flagged_for_review = True)
    reviews_pending = db.query(func.count(Agent.id)).filter(
        Agent.flagged_for_review == True,
        Agent.lifecycle_status != "deprovisioned"
    ).scalar() or 0

    # 7. Average security score
    avg_score = db.query(func.avg(Agent.security_score)).filter(Agent.lifecycle_status == "active").scalar()
    average_security_score = round(float(avg_score), 1) if avg_score is not None else 100.0

    # 8. Risk distribution
    risk_rows = db.query(
        Agent.risk_level,
        func.count(Agent.id)
    ).filter(Agent.lifecycle_status != "deprovisioned").group_by(Agent.risk_level).all()

    risk_dist = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for level, count in risk_rows:
        if level in risk_dist:
            risk_dist[level] = count

    # 9. Recent 10 audit logs
    recent_audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "suspended_agents": suspended_agents,
        "expired_credentials": expired_credentials,
        "credentials_near_expiry": credentials_near_expiry,
        "reviews_pending": reviews_pending,
        "average_security_score": average_security_score,
        "risk_distribution": risk_dist,
        "recent_audit_activity": recent_audits
    }
