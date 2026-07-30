import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.database.session import Base

def generate_credential_id():
    return f"crd_{uuid.uuid4().hex[:12]}"

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True, default=generate_credential_id)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    credential_lookup_id = Column(String, unique=True, index=True, nullable=False)
    credential_hash = Column(String, nullable=False)
    active = Column(Boolean, default=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    rotated_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
