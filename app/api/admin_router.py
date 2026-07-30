from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_superadmin
from app.auth.password import hash_password
from app.schemas.admin_schemas import (
    AdminCreateRequest,
    AdminUpdateRequest,
    AdminResponse,
    AdminListResponse
)
from app.repository.admin_repository import (
    get_admin_by_email,
    get_admin_by_id,
    create_admin
)
from app.models.admin import Admin

router = APIRouter(prefix="/admins", tags=["Admin Account Management"])

@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin_account(
    payload: AdminCreateRequest,
    db: Session = Depends(get_db),
    current_superadmin: Admin = Depends(require_superadmin)
):
    existing = get_admin_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Admin with email '{payload.email}' already exists."
        )

    if payload.role not in ("superadmin", "admin", "auditor"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'superadmin', 'admin', or 'auditor'."
        )

    hashed = hash_password(payload.password)
    new_admin = create_admin(
        db=db,
        email=payload.email,
        hashed_password=hashed,
        role=payload.role,
        org_id=payload.org_id or "org_default"
    )
    return AdminResponse.model_validate(new_admin)

@router.get("", response_model=AdminListResponse)
def list_admin_accounts(
    db: Session = Depends(get_db),
    current_superadmin: Admin = Depends(require_superadmin)
):
    admins = db.query(Admin).order_by(Admin.created_at.desc()).all()
    responses = [AdminResponse.model_validate(a) for a in admins]
    return AdminListResponse(total=len(responses), admins=responses)

@router.put("/{admin_id}", response_model=AdminResponse)
def update_admin_account(
    admin_id: str,
    payload: AdminUpdateRequest,
    db: Session = Depends(get_db),
    current_superadmin: Admin = Depends(require_superadmin)
):
    target = get_admin_by_id(db, admin_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin account '{admin_id}' not found."
        )

    if payload.role:
        if payload.role not in ("superadmin", "admin", "auditor"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'superadmin', 'admin', or 'auditor'."
            )
        target.role = payload.role

    if payload.is_active is not None:
        target.is_active = payload.is_active

    db.commit()
    db.refresh(target)
    return AdminResponse.model_validate(target)
