import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, JSON, DateTime
from app.database.session import Base

def generate_audit_id():
    return f"aud_{uuid.uuid4().hex[:12]}"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_audit_id)
    action = Column(String, index=True, nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    agent_id = Column(String, index=True, nullable=True)
    performed_by = Column(String, index=True, nullable=True)
    status_code = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # "success" | "failure"
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
