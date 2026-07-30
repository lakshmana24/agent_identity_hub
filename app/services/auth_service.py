from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from app.schemas.auth_schemas import LoginRequest, TokenResponse, RefreshTokenRequest
from app.repository.admin_repository import get_admin_by_email, get_admin_by_id
from app.auth.password import verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.config.settings import settings

def authenticate_admin(db: Session, payload: LoginRequest) -> TokenResponse:
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    admin = get_admin_by_email(db, email=payload.email)
    if not admin:
        raise generic_error

    if not verify_password(payload.password, admin.hashed_password):
        raise generic_error

    token_payload = {
        "sub": admin.id,
        "email": admin.email,
        "role": admin.role,
        "org_id": admin.org_id
    }

    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

def refresh_access_token(db: Session, payload: RefreshTokenRequest) -> dict:
    invalid_token_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise invalid_token_error
        admin_id: str = decoded.get("sub")
        if not admin_id:
            raise invalid_token_error
    except JWTError:
        raise invalid_token_error

    admin = get_admin_by_id(db, admin_id=admin_id)
    if not admin:
        raise invalid_token_error

    token_payload = {
        "sub": admin.id,
        "email": admin.email,
        "role": admin.role,
        "org_id": admin.org_id
    }
    new_access_token = create_access_token(data=token_payload)

    return {
        "access_token": new_access_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
