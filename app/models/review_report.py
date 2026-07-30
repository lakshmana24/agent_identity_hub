import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database.session import Base

def generate_review_id():
    return f"rev_{uuid.uuid4().hex[:12]}"

class ReviewReport(Base):
    __tablename__ = "review_reports"

    id = Column(String, primary_key=True, default=generate_review_id)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    agent_name = Column(String, nullable=False)
    security_score = Column(Integer, nullable=False)
    recommendation = Column(String, nullable=False)  # "renew" | "review permissions" | "deprovision — inactive"
    reasoning = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
