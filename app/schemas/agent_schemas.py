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
    owning_team: str = "Growth"
    requested_scopes: List[str]
    expiry_date: Optional[datetime] = None  # Agent identity authorized lifetime (ISO 8601 string or default 1yr)
    owner: Optional[str] = "admin@company.com"
    model_provider: Optional[str] = "Other"
    model_name: Optional[str] = "unknown"
    tools: Optional[List[str]] = []
    agent_endpoint_url: Optional[str] = None
    deployment_environment: Optional[str] = "production"
    risk_level: Optional[str] = None
    risk_level_source: Optional[str] = "ai_recommended"
    risk_reasoning: Optional[str] = None
    description: Optional[str] = None

class AgentUpdateRequest(BaseModel):
    agent_name: Optional[str] = None
    purpose: Optional[str] = None
    owning_team: Optional[str] = None
    expiry_date: Optional[datetime] = None
    owner: Optional[str] = None
    requested_scopes: Optional[List[str]] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    tools: Optional[List[str]] = None
    agent_endpoint_url: Optional[str] = None
    deployment_environment: Optional[str] = None
    risk_level: Optional[str] = None
    risk_level_source: Optional[str] = None
    risk_reasoning: Optional[str] = None
    description: Optional[str] = None

class IdentityCard(BaseModel):
    agent_id: str
    agent_name: str
    owning_team: str = "Growth"
    purpose: str
    owner: str = "admin@company.com"
    expiry_date: Optional[datetime] = None
    model_provider: str = "Other"
    model_name: str = "unknown"
    tools: List[str] = []
    agent_endpoint_url: Optional[str] = None
    deployment_environment: str = "production"
    description: Optional[str] = None
    risk_level: str
    risk_level_source: str = "ai_recommended"
    risk_reasoning: Optional[str] = None
    allowed_scopes: List[str]
    credential_status: str  # "not_issued", "active", "expired", "revoked"
    active_credential_expires_at: Optional[datetime] = None  # Credential's own expires_at
    lifecycle_status: str  # "active", "suspended", "deprovisioned"
    security_score: int
    flagged_for_review: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    agents: List[IdentityCard]
