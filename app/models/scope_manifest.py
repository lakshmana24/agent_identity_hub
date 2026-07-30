import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database.session import Base

def generate_scope_id():
    return f"scp_{uuid.uuid4().hex[:12]}"

class ScopeManifest(Base):
    __tablename__ = "scope_manifest"

    id = Column(String, primary_key=True, default=generate_scope_id)
    scope_name = Column(String, unique=True, index=True, nullable=False)
    action_type = Column(String, nullable=False)  # "read" | "write"
    description = Column(String, nullable=False)
    risk_level = Column(String, nullable=False, default="Low")  # Low, Medium, High, Critical
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
