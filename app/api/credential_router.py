from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin, require_write_access
from app.schemas.credential_schemas import (
    CredentialGenerateRequest,
    CredentialGenerateResponse,
    CredentialRotateRequest,
    CredentialRenewRequest,
    CredentialRevokeRequest,
    CredentialValidateRequest,
    CredentialValidationResult
)
from app.services.credential_service import (
    generate_credential_service,
    rotate_credential_service,
    renew_credential_service,
    revoke_credential_service,
    validate_credential_service
)
from app.models.admin import Admin

router = APIRouter(prefix="/credentials", tags=["Credential Management"])

@router.post("/generate", response_model=CredentialGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_credential(
    payload: CredentialGenerateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_write_access)
):
    return generate_credential_service(db, payload)

@router.post("/rotate", response_model=CredentialGenerateResponse)
def rotate_credential(
    payload: CredentialRotateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_write_access)
):
    return rotate_credential_service(db, payload)

@router.post("/renew")
def renew_credential(
    payload: CredentialRenewRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_write_access)
):
    return renew_credential_service(db, payload)

@router.post("/revoke")
def revoke_credential(
    payload: CredentialRevokeRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_write_access)
):
    return revoke_credential_service(db, payload)

@router.post("/validate", response_model=CredentialValidationResult)
def validate_credential(
    payload: CredentialValidateRequest,
    db: Session = Depends(get_db)
):
    return validate_credential_service(db, payload)
