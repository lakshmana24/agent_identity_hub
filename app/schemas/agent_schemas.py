from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ScopeCreateRequest(BaseModel):
    scope_name: str
    action_type: str  # "read" | "write"
    description: str
    risk_level: str   # "Low" | "Medium" | "High" | "Critical"

class ScopeResponse(BaseModel):
    id: str
    scope_name: str
    action_type: str
    description: str
    risk_level: str
    deprecated: bool = False

    model_config = ConfigDict(from_attributes=True)

class AgentCreateRequest(BaseModel):
    agent_name: str
    purpose: str
    department: str
    owner: str
    requested_scopes: List[str]
    model_provider: Optional[str] = "Other"
    model_name: Optional[str] = "unknown"
    tools: Optional[List[str]] = []
    agent_endpoint_url: Optional[str] = None
    deployment_environment: Optional[str] = "production"
    risk_level: Optional[str] = None  # If provided by admin/wizard
    risk_level_source: Optional[str] = "ai_recommended"  # "ai_recommended" | "admin_override"
    description: Optional[str] = None

class AgentUpdateRequest(BaseModel):
    purpose: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    requested_scopes: Optional[List[str]] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    tools: Optional[List[str]] = None
    agent_endpoint_url: Optional[str] = None
    deployment_environment: Optional[str] = None
    risk_level: Optional[str] = None
    risk_level_source: Optional[str] = None
    description: Optional[str] = None

class IdentityCard(BaseModel):
    agent_id: str
    agent_name: str
    model_provider: str = "Other"
    model_name: str = "unknown"
    tools: List[str] = []
    agent_endpoint_url: Optional[str] = None
    deployment_environment: str = "production"
    purpose: str
    department: str
    owner: str
    description: Optional[str] = None
    risk_level: str
    risk_level_source: str = "ai_recommended"
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
