from typing import List, Dict
from pydantic import BaseModel, ConfigDict
from app.schemas.audit_schemas import AuditLogResponse

class DashboardMetricsResponse(BaseModel):
    total_agents: int
    active_agents: int
    suspended_agents: int
    expired_credentials: int
    credentials_near_expiry: int
    reviews_pending: int
    average_security_score: float
    recent_audit_activity: List[AuditLogResponse]
    risk_distribution: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)
