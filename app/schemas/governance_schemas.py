from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class GovernanceAnalyzeRequest(BaseModel):
    agent_id: str

class ScoreBreakdownItem(BaseModel):
    rule: str
    penalty: int
    reason: str

class SecurityScoreResponse(BaseModel):
    agent_id: str
    security_score: int
    risk_level: str
    breakdown: List[ScoreBreakdownItem]

class GovernanceAnalysisResult(BaseModel):
    agent_id: str
    agent_name: str
    security_score: int
    risk_level: str
    issues_detected: List[str]
    recommendations: List[str]
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)
