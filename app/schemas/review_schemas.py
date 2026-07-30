from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ReviewReportResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    security_score: int
    recommendation: str
    reasoning: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReviewReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    reports: List[ReviewReportResponse]

class StaleAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    owning_team: str = "Growth"
    department: str = "General"
    owner: str = "admin@company.com"
    last_used_at: Optional[datetime] = None
    days_inactive: int
    call_count: int = 0
    flagged_for_review: bool = True

    model_config = ConfigDict(from_attributes=True)
