from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth_schemas import LoginRequest, TokenResponse, RefreshTokenRequest, AdminResponse
from app.services.auth_service import authenticate_admin, refresh_access_token
from app.auth.dependencies import get_current_admin
from app.models.admin import Admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return authenticate_admin(db, payload)

@router.post("/refresh-token")
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, payload)

@router.get("/me", response_model=AdminResponse)
def get_me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin
