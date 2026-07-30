from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AdminResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    org_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
