from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.credential import Credential

def get_credential_by_lookup_id(db: Session, lookup_id: str) -> Optional[Credential]:
    return db.query(Credential).filter(Credential.credential_lookup_id == lookup_id).first()

def get_active_credential_by_agent_id(db: Session, agent_id: str) -> Optional[Credential]:
    return db.query(Credential).filter(
        Credential.agent_id == agent_id,
        Credential.active == True
    ).first()

def get_latest_credential_by_agent_id(db: Session, agent_id: str) -> Optional[Credential]:
    return db.query(Credential).filter(
        Credential.agent_id == agent_id
    ).order_by(Credential.created_at.desc()).first()

def deactivate_agent_credentials(db: Session, agent_id: str, rotated: bool = False, reason: Optional[str] = None) -> None:
    now = datetime.now(timezone.utc)
    active_creds = db.query(Credential).filter(
        Credential.agent_id == agent_id,
        Credential.active == True
    ).all()
    for c in active_creds:
        c.active = False
        if rotated:
            c.rotated_at = now
        else:
            c.revoked_at = now
            c.revocation_reason = reason or "Deactivated for new issuance"
    db.commit()

def create_credential(db: Session, cred_data: dict) -> Credential:
    cred = Credential(**cred_data)
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred

def update_credential(db: Session, credential: Credential, update_dict: dict) -> Credential:
    for key, value in update_dict.items():
        setattr(credential, key, value)
    db.commit()
    db.refresh(credential)
    return credential
