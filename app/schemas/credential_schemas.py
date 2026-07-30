from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CredentialGenerateRequest(BaseModel):
    agent_id: str
    expires_in_days: int = Field(default=90, ge=1, le=365)

class CredentialGenerateResponse(BaseModel):
    agent_id: str
    credential: str
    expires_at: datetime
    warning: str = "This credential will not be shown again. Store it securely."

class CredentialRotateRequest(BaseModel):
    agent_id: str

class CredentialRenewRequest(BaseModel):
    agent_id: str
    extend_days: int = Field(default=30, ge=1, le=365)

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
