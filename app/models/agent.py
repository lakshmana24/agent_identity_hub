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
    owning_team = Column(String, index=True, nullable=False, default="Growth")
    purpose = Column(String, nullable=False)
    owner = Column(String, nullable=False, default="admin@company.com")
    description = Column(String, nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # Agent identity authorized lifetime
    
    # Optional metadata
    model_provider = Column(String, nullable=False, default="Other")
    model_name = Column(String, nullable=False, default="unknown")
    tools = Column(JSON, nullable=False, default=list)
    agent_endpoint_url = Column(String, nullable=True)
    deployment_environment = Column(String, nullable=False, default="production")

    # Governance & Status
    risk_level = Column(String, nullable=False, default="Low")  # Low, Medium, High, Critical
    risk_level_source = Column(String, nullable=False, default="ai_recommended")  # ai_recommended, admin_override
    risk_reasoning = Column(String, nullable=True)  # Specific risk explanation under risk badge
    allowed_scopes = Column(JSON, nullable=False, default=list)  # e.g. ["crm:read", "tickets:write"]
    lifecycle_status = Column(String, nullable=False, default="active")  # active, suspended, deprovisioned
    security_score = Column(Integer, nullable=False, default=100)
    flagged_for_review = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
