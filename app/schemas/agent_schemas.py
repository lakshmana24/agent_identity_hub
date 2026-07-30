from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ScopeResponse(BaseModel):
    id: str
    scope_name: str
    action_type: str
    description: str
    risk_level: str

    model_config = ConfigDict(from_attributes=True)

class AgentCreateRequest(BaseModel):
    agent_name: str
    purpose: str
    department: str
    owner: str
    requested_scopes: List[str]
    description: Optional[str] = None

class AgentUpdateRequest(BaseModel):
    purpose: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    requested_scopes: Optional[List[str]] = None
    description: Optional[str] = None

class IdentityCard(BaseModel):
    agent_id: str
    agent_name: str
    purpose: str
    department: str
    owner: str
    description: Optional[str] = None
    risk_level: str
    allowed_scopes: List[str]
    credential_status: str  # "not_issued", "active", "expired", "revoked"
    expiry_date: Optional[datetime] = None
    lifecycle_status: str  # "active", "suspended", "deprovisioned"
    security_score: int
    flagged_for_review: bool = False
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    agents: List[IdentityCard]
