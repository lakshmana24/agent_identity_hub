from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ScopeRecommendationRequest(BaseModel):
    purpose: str

class ScopeRecommendationResponse(BaseModel):
    recommended_scopes: List[str]
    rejected_scopes: List[str]
    risk_level: str  # "Low" | "Medium" | "High" | "Critical"
    reasoning: str

    model_config = ConfigDict(from_attributes=True)

class IdentitySummaryRequest(BaseModel):
    agent_name: str
    purpose: str
    department: str
    scopes: List[str]
    risk_level: str

class IdentitySummaryResponse(BaseModel):
    summary: str
