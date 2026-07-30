from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "admin"  # "superadmin" | "admin" | "auditor"
    org_id: Optional[str] = "org_default"

class AdminUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AdminResponse(BaseModel):
    id: str
    email: str
    role: str
    org_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AdminListResponse(BaseModel):
    total: int
    admins: List[AdminResponse]
