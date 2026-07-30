from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Ensures all models are registered on Base.metadata
from app.main import app
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.models.credential import Credential
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

@pytest.fixture
def auth_headers(db_session):
    admin = Admin(
        email="govadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_agent(client, auth_headers):
    resp = client.post("/agents", json={
        "agent_name": "Governance Test Agent",
        "purpose": "Processes customer refunds",
        "department": "Finance",
        "owner": "gov@company.com",
        "requested_scopes": ["crm:read", "tickets:read"]
    }, headers=auth_headers)
    return resp.json()

def test_compute_security_score_perfect(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    # Issue active credential
    client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)

    resp = client.get(f"/governance/security-score/{agent_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["security_score"] == 100
    assert len(data["breakdown"]) == 0

def test_compute_security_score_no_active_credential(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]

    resp = client.get(f"/governance/security-score/{agent_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Deducts 15 for NO_ACTIVE_CREDENTIAL
    assert data["security_score"] == 85
    assert any(b["rule"] == "NO_ACTIVE_CREDENTIAL" for b in data["breakdown"])

def test_compute_security_score_old_credential(client, auth_headers, test_agent, db_session):
    agent_id = test_agent["agent_id"]
    client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)

    # Backdate credential creation date to 100 days ago
    cred = db_session.query(Credential).filter(Credential.agent_id == agent_id).first()
    cred.created_at = datetime.now(timezone.utc) - timedelta(days=100)
    db_session.commit()

    resp = client.get(f"/governance/security-score/{agent_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["security_score"] == 80
    assert any(b["rule"] == "CREDENTIAL_AGE_OVER_90_DAYS" for b in data["breakdown"])

def test_analyze_governance_endpoint(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]

    resp = client.post("/governance/analyze", json={"agent_id": agent_id}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == agent_id
    assert len(data["recommendations"]) > 0
    assert any("generate" in r.lower() for r in data["recommendations"])
