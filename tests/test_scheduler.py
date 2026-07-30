from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.main import app
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.models.agent import Agent
from app.models.credential import Credential
from app.models.review_report import ReviewReport
from app.auth.password import hash_password
from app.auth.jwt_handler import create_access_token
from app.repository.agent_repository import seed_default_scopes
from app.scheduler.jobs import (
    check_expired_credentials_job,
    detect_stale_agents_job,
    generate_governance_reviews_job
)

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_default_scopes(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    import app.scheduler.jobs as sj
    import app.middleware.audit_middleware as am
    def _override_session_local():
        return db_session

    original_sj_session = sj.SessionLocal
    original_am_session = am.SessionLocal
    sj.SessionLocal = _override_session_local
    am.SessionLocal = _override_session_local

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    sj.SessionLocal = original_sj_session
    am.SessionLocal = original_am_session

@pytest.fixture
def auth_headers(db_session):
    admin = Admin(
        email="schedadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_check_expired_credentials_job(client, auth_headers, db_session):
    # Register agent & issue credential
    reg = client.post("/agents", json={
        "agent_name": "Expiry Test Bot",
        "purpose": "Testing auto-expiry",
        "department": "Security",
        "owner": "sec@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers).json()
    agent_id = reg["agent_id"]

    client.post("/credentials/generate", json={"agent_id": agent_id, "expires_in_days": 1}, headers=auth_headers)

    # Backdate credential expiration to yesterday
    cred = db_session.query(Credential).filter(Credential.agent_id == agent_id).first()
    cred.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    # Run job
    check_expired_credentials_job()

    # Re-query credential to check updated active status
    updated_cred = db_session.query(Credential).filter(Credential.agent_id == agent_id).first()
    assert updated_cred.active is False

def test_detect_stale_agents_job(client, auth_headers, db_session):
    # Register agent
    reg = client.post("/agents", json={
        "agent_name": "Stale Agent Bot",
        "purpose": "Testing stale agent detection",
        "department": "Legacy",
        "owner": "old@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers).json()
    agent_id = reg["agent_id"]

    # Backdate agent created_at to 35 days ago
    agent_row = db_session.query(Agent).filter(Agent.id == agent_id).first()
    agent_row.created_at = datetime.now(timezone.utc) - timedelta(days=35)
    db_session.commit()

    # Run job
    detect_stale_agents_job()

    # Re-query agent to check updated flagged_for_review status
    updated_agent = db_session.query(Agent).filter(Agent.id == agent_id).first()
    assert updated_agent.flagged_for_review is True

    # Check GET /reviews/stale-agents
    stale_resp = client.get("/reviews/stale-agents", headers=auth_headers)
    assert stale_resp.status_code == 200
    stale_list = stale_resp.json()
    assert any(s["agent_id"] == agent_id for s in stale_list)

def test_manual_review_trigger(client, auth_headers):
    # Register agent
    client.post("/agents", json={
        "agent_name": "Review Target Agent",
        "purpose": "Testing governance review generation",
        "department": "IT",
        "owner": "it@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers)

    # Call POST /reviews/run
    run_resp = client.post("/reviews/run", headers=auth_headers)
    assert run_resp.status_code == 200

    # Query GET /reviews
    rev_resp = client.get("/reviews", headers=auth_headers)
    assert rev_resp.status_code == 200
    data = rev_resp.json()
    assert data["total"] >= 1
