from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.credential_schemas import (
    CredentialGenerateRequest,
    CredentialGenerateResponse,
    CredentialRotateRequest,
    CredentialRenewRequest,
    CredentialRevokeRequest,
    CredentialValidateRequest,
    CredentialValidationResult
)
from app.repository.credential_repository import (
    get_credential_by_lookup_id,
    get_active_credential_by_agent_id,
    deactivate_agent_credentials,
    create_credential,
    update_credential
)
from app.repository.agent_repository import get_agent_by_id
from app.utils.credential_generator import generate_credential_pair, split_credential
from app.auth.password import hash_password, verify_password

def generate_credential_service(db: Session, payload: CredentialGenerateRequest) -> CredentialGenerateResponse:
    agent = get_agent_by_id(db, payload.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{payload.agent_id}' not found.")
    if agent.lifecycle_status == "deprovisioned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot generate credentials for a deprovisioned agent.")

    # Deactivate prior active credentials
    deactivate_agent_credentials(db, agent.id)

    raw_credential, lookup_id, secret = generate_credential_pair(agent.id)
    secret_hash = hash_password(secret)
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    cred_data = {
        "agent_id": agent.id,
        "credential_lookup_id": lookup_id,
        "credential_hash": secret_hash,
        "active": True,
        "expires_at": expires_at
    }
    create_credential(db, cred_data)

    return CredentialGenerateResponse(
        agent_id=agent.id,
        credential=raw_credential,
        expires_at=expires_at
    )

def rotate_credential_service(db: Session, payload: CredentialRotateRequest) -> CredentialGenerateResponse:
    agent = get_agent_by_id(db, payload.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{payload.agent_id}' not found.")
    if agent.lifecycle_status == "deprovisioned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot rotate credentials for a deprovisioned agent.")

    # Mark old credential rotated
    deactivate_agent_credentials(db, agent.id, rotated=True)

    # Generate new credential (default 90 days)
    raw_credential, lookup_id, secret = generate_credential_pair(agent.id)
    secret_hash = hash_password(secret)
    expires_at = datetime.now(timezone.utc) + timedelta(days=90)

    cred_data = {
        "agent_id": agent.id,
        "credential_lookup_id": lookup_id,
        "credential_hash": secret_hash,
        "active": True,
        "expires_at": expires_at
    }
    create_credential(db, cred_data)

    return CredentialGenerateResponse(
        agent_id=agent.id,
        credential=raw_credential,
        expires_at=expires_at
    )

def renew_credential_service(db: Session, payload: CredentialRenewRequest) -> dict:
    cred = get_active_credential_by_agent_id(db, payload.agent_id)
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active credential found for agent '{payload.agent_id}'.")

    exp = cred.expires_at
    if exp and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    new_expires_at = exp + timedelta(days=payload.extend_days)
    update_credential(db, cred, {"expires_at": new_expires_at})

    return {
        "agent_id": payload.agent_id,
        "new_expires_at": new_expires_at
    }

def revoke_credential_service(db: Session, payload: CredentialRevokeRequest) -> dict:
    now = datetime.now(timezone.utc)
    deactivate_agent_credentials(db, payload.agent_id, rotated=False, reason=payload.reason)
    return {
        "status": "revoked",
        "agent_id": payload.agent_id,
        "revoked_at": now
    }

def validate_credential_service(db: Session, payload: CredentialValidateRequest) -> CredentialValidationResult:
    # 1. Parse lookup_id and secret
    lookup_id, secret = split_credential(payload.credential)
    if not lookup_id or not secret:
        return CredentialValidationResult(valid=False, reason="not_found")

    # 2. Query credential by lookup_id
    cred = get_credential_by_lookup_id(db, lookup_id)
    if not cred:
        return CredentialValidationResult(valid=False, reason="not_found")

    # 3. Verify secret against hash
    if not verify_password(secret, cred.credential_hash):
        return CredentialValidationResult(valid=False, reason="invalid_secret")

    # 4. Check active status
    if not cred.active:
        return CredentialValidationResult(valid=False, reason="revoked")

    # 5. Check expiration timestamp
    now = datetime.now(timezone.utc)
    exp = cred.expires_at
    if exp and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp < now:
        return CredentialValidationResult(valid=False, reason="expired")

    # 6. Check agent status & scope authorization
    agent = get_agent_by_id(db, cred.agent_id)
    if not agent or agent.lifecycle_status != "active":
        return CredentialValidationResult(valid=False, reason="revoked")

    if payload.requested_scope not in (agent.allowed_scopes or []):
        return CredentialValidationResult(valid=False, reason="scope_not_authorized")

    # All checks pass
    return CredentialValidationResult(
        valid=True,
        agent_id=agent.id,
        scopes=agent.allowed_scopes
    )
