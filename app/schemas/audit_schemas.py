from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class AuditLogResponse(BaseModel):
    id: str
    action: str
    method: str
    path: str
    agent_id: Optional[str] = None
    performed_by: Optional[str] = None
    status_code: int
    status: str
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: List[AuditLogResponse]
