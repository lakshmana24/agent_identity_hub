from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CredentialGenerateRequest(BaseModel):
    agent_id: str
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)
    expires_at: Optional[datetime] = None  # Optional testing override (ISO 8601 string)

class CredentialGenerateResponse(BaseModel):
    agent_id: str
    credential: str
    expires_at: datetime
    warning: str = "This credential secret will not be shown again. Store it securely."

class CredentialRotateRequest(BaseModel):
    agent_id: str
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)
    expires_at: Optional[datetime] = None

class CredentialRenewRequest(BaseModel):
    agent_id: str
    extend_days: Optional[int] = Field(default=30, ge=1, le=365)
    expires_at: Optional[datetime] = None

class CredentialRevokeRequest(BaseModel):
    agent_id: str
    reason: str = "Admin requested revocation"

class CredentialValidateRequest(BaseModel):
    credential: str
    requested_scope: str

class CredentialValidationResult(BaseModel):
    valid: bool
    reason: Optional[str] = None
    agent_id: Optional[str] = None
    scopes: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
