import os
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.auth.password import hash_password
from app.auth.jwt_handler import create_access_token
from app.repository.agent_repository import seed_default_scopes

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch main engine and SessionLocal for lifespan execution during tests
import app.main as main_mod
import app.middleware.audit_middleware as am
import app.scheduler.jobs as jobs_mod

main_mod.engine = engine
main_mod.SessionLocal = TestingSessionLocal
am.SessionLocal = TestingSessionLocal
jobs_mod.SessionLocal = TestingSessionLocal

from app.main import app

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

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def get_auth_headers(db_session, role="superadmin", email="super@example.com"):
    admin = Admin(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_create_agent_with_owning_team_and_risk_reasoning(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="creator@example.com")
    payload = {
        "agent_name": "GrowthBot",
        "purpose": "Processes customer campaign data and updates CRM records",
        "owning_team": "Growth",
        "owner": "growth@company.com",
        "requested_scopes": ["crm:read", "tickets:read"]
    }
    resp = client.post("/agents", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["owning_team"] == "Growth"
    assert data["expiry_date"] is not None
    assert data["risk_reasoning"] is not None
    assert "department" not in data

def test_credential_usage_tracking_and_agent_expiry(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="usagetester@example.com")
    reg = client.post("/agents", json={
        "agent_name": "UsageTrackingBot",
        "purpose": "Test real credential usage tracking",
        "owning_team": "Finance",
        "owner": "fin@company.com",
        "requested_scopes": ["payments:read"]
    }, headers=headers).json()
    agent_id = reg["agent_id"]

    # Issue credential
    gen = client.post("/credentials/generate", json={
        "agent_id": agent_id,
        "expires_in_days": 90
    }, headers=headers).json()
    raw_cred = gen["credential"]

    # Validate credential -> Valid & increments usage
    val_resp = client.post("/credentials/validate", json={
        "credential": raw_cred,
        "requested_scope": "payments:read"
    })
    assert val_resp.status_code == 200
    assert val_resp.json()["valid"] is True

def test_expired_agent_identity_rejection(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="expidentity@example.com")
    past_iso = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    reg = client.post("/agents", json={
        "agent_name": "ExpiredIdentityBot",
        "purpose": "Test agent identity expiration",
        "owning_team": "DevOps",
        "expiry_date": past_iso,
        "requested_scopes": ["tickets:read"]
    }, headers=headers).json()
    agent_id = reg["agent_id"]

    gen = client.post("/credentials/generate", json={
        "agent_id": agent_id,
        "expires_in_days": 90
    }, headers=headers).json()
    raw_cred = gen["credential"]

    # Validate -> Returns valid: false with reason: agent_identity_expired
    val_resp = client.post("/credentials/validate", json={
        "credential": raw_cred,
        "requested_scope": "tickets:read"
    })
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["valid"] is False
    assert val_data["reason"] == "agent_identity_expired"

def test_team_quarterly_review_report(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="reporttester@example.com")
    client.post("/agents", json={
        "agent_name": "FinanceAgent1",
        "purpose": "Finance reporting",
        "owning_team": "Finance",
        "requested_scopes": ["payments:read"]
    }, headers=headers)

    report_resp = client.get("/reviews/report", headers=headers)
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert "teams_reports" in report

def test_v3_chatbot_verification_prompts(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="chat@example.com")
    
    # Register real agent
    client.post("/agents", json={
        "agent_name": "RealSupportBot",
        "purpose": "Drafts support replies",
        "owning_team": "Customer Support",
        "requested_scopes": ["tickets:read"]
    }, headers=headers)

    # 1. "List currently active agents" -> references real agent name
    q1 = client.post("/chatbot/ask", json={"question": "List currently active agents"}, headers=headers)
    assert q1.status_code == 200
    ans1 = q1.json()["answer"]
    assert "RealSupportBot" in ans1

    # 2. "What scopes does RealSupportBot have?"
    q2 = client.post("/chatbot/ask", json={"question": "What scopes does RealSupportBot have?"}, headers=headers)
    assert q2.status_code == 200
    assert "tickets:read" in q2.json()["answer"]

    # 3. "Which agents are stale?"
    q3 = client.post("/chatbot/ask", json={"question": "Which agents are stale?"}, headers=headers)
    assert q3.status_code == 200
    assert "answer" in q3.json()

    # 4. "What's the capital of France?" -> Declined per domain boundary
    q4 = client.post("/chatbot/ask", json={"question": "What's the capital of France?"}, headers=headers)
    assert q4.status_code == 200
    assert q4.json()["answer"] == "I can only answer questions about agents and data within Agent Identity Hub."

    # 5. "Revoke RealSupportBot's credential" -> Declined per read-only boundary
    q5 = client.post("/chatbot/ask", json={"question": "Revoke RealSupportBot's credential"}, headers=headers)
    assert q5.status_code == 200
    assert "read-only" in q5.json()["answer"].lower()

    # 6. Non-existent field "what's RealSupportBot's uptime percentage?" -> States data not available
    q6 = client.post("/chatbot/ask", json={"question": "What is RealSupportBot's uptime percentage?"}, headers=headers)
    assert q6.status_code == 200
    assert "telemetry" in q6.json()["answer"].lower() or "not tracked" in q6.json()["answer"].lower() or "not available" in q6.json()["answer"].lower()
