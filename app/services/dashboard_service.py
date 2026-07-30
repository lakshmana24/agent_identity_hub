from sqlalchemy.orm import Session
from app.schemas.dashboard_schemas import DashboardMetricsResponse
from app.schemas.audit_schemas import AuditLogResponse
from app.repository.dashboard_repository import get_dashboard_metrics_data

def get_dashboard_service(db: Session) -> DashboardMetricsResponse:
    data = get_dashboard_metrics_data(db)
    recent_audits = [AuditLogResponse.model_validate(log) for log in data["recent_audit_activity"]]

    return DashboardMetricsResponse(
        total_agents=data["total_agents"],
        active_agents=data["active_agents"],
        suspended_agents=data["suspended_agents"],
        expired_credentials=data["expired_credentials"],
        credentials_near_expiry=data["credentials_near_expiry"],
        reviews_pending=data["reviews_pending"],
        average_security_score=data["average_security_score"],
        recent_audit_activity=recent_audits,
        risk_distribution=data["risk_distribution"]
    )
