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
    department: str
    owner: str
    last_activity_at: datetime
    days_inactive: int
    flagged_for_review: bool

    model_config = ConfigDict(from_attributes=True)
