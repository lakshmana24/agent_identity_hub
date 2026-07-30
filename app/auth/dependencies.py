from typing import List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.jwt_handler import decode_token
from app.repository.admin_repository import get_admin_by_id
from app.models.admin import Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = get_admin_by_id(db, admin_id=admin_id)
    if admin is None or not getattr(admin, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or credentials invalid."
        )
    return admin

def require_role(roles: Union[str, List[str]]):
    allowed = [roles] if isinstance(roles, str) else roles
    def role_checker(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role not in allowed and current_admin.role != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{current_admin.role}'. Required: {allowed}."
            )
        return current_admin
    return role_checker

def require_write_access(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    if current_admin.role == "auditor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor role is read-only. Mutating actions are prohibited."
        )
    return current_admin

def require_superadmin(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    if current_admin.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privilege required for this action."
        )
    return current_admin
