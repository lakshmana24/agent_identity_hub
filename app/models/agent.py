import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime
from app.database.session import Base

def generate_agent_id():
    return f"agt_{uuid.uuid4().hex[:8]}"

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_agent_id)
    agent_name = Column(String, index=True, nullable=False)
    purpose = Column(String, nullable=False)
    department = Column(String, index=True, nullable=False)
    owner = Column(String, nullable=False)
    description = Column(String, nullable=True)
    risk_level = Column(String, nullable=False, default="Low")  # Low, Medium, High, Critical
    allowed_scopes = Column(JSON, nullable=False, default=list)  # e.g. ["crm:read", "tickets:write"]
    lifecycle_status = Column(String, nullable=False, default="active")  # active, suspended, deprovisioned
    security_score = Column(Integer, nullable=False, default=100)
    ai_summary = Column(String, nullable=True)
    flagged_for_review = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
