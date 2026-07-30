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
        email="credadmin@example.com",
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
        "agent_name": "Credential Test Agent",
        "purpose": "Testing credential issuance",
        "department": "Security",
        "owner": "sec@company.com",
        "requested_scopes": ["crm:read", "tickets:read"]
    }, headers=auth_headers)
    return resp.json()

def test_generate_credential(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={
        "agent_id": agent_id,
        "expires_in_days": 30
    }, headers=auth_headers)

    assert gen_resp.status_code == 201
    data = gen_resp.json()
    assert "credential" in data
    assert data["credential"].startswith("aih_")
    assert data["agent_id"] == agent_id

    # Check Identity Card reflects active credential status
    detail_resp = client.get(f"/agents/{agent_id}", headers=auth_headers)
    assert detail_resp.json()["credential_status"] == "active"

def test_validate_credential_valid(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)
    cred_str = gen_resp.json()["credential"]

    val_resp = client.post("/credentials/validate", json={
        "credential": cred_str,
        "requested_scope": "crm:read"
    })
    assert val_resp.status_code == 200
    res = val_resp.json()
    assert res["valid"] is True
    assert res["agent_id"] == agent_id
    assert "crm:read" in res["scopes"]

def test_validate_credential_unauthorized_scope(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)
    cred_str = gen_resp.json()["credential"]

    # crm:write is NOT in agent's allowed_scopes (agent only has crm:read and tickets:read)
    val_resp = client.post("/credentials/validate", json={
        "credential": cred_str,
        "requested_scope": "crm:write"
    })
    assert val_resp.status_code == 200
    res = val_resp.json()
    assert res["valid"] is False
    assert res["reason"] == "scope_not_authorized"

def test_validate_credential_expired(client, auth_headers, test_agent, db_session):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)
    cred_str = gen_resp.json()["credential"]

    # Manually backdate expires_at in DB
    cred_row = db_session.query(Credential).filter(Credential.agent_id == agent_id).first()
    cred_row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    val_resp = client.post("/credentials/validate", json={
        "credential": cred_str,
        "requested_scope": "crm:read"
    })
    assert val_resp.status_code == 200
    res = val_resp.json()
    assert res["valid"] is False
    assert res["reason"] == "expired"

def test_revoke_credential(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)
    cred_str = gen_resp.json()["credential"]

    # Revoke
    rev_resp = client.post("/credentials/revoke", json={
        "agent_id": agent_id,
        "reason": "Compromised credential"
    }, headers=auth_headers)
    assert rev_resp.status_code == 200
    assert rev_resp.json()["status"] == "revoked"

    # Validate again
    val_resp = client.post("/credentials/validate", json={
        "credential": cred_str,
        "requested_scope": "crm:read"
    })
    assert val_resp.status_code == 200
    res = val_resp.json()
    assert res["valid"] is False
    assert res["reason"] == "revoked"

def test_rotate_credential(client, auth_headers, test_agent):
    agent_id = test_agent["agent_id"]
    gen_resp = client.post("/credentials/generate", json={"agent_id": agent_id}, headers=auth_headers)
    old_cred = gen_resp.json()["credential"]

    # Rotate
    rot_resp = client.post("/credentials/rotate", json={"agent_id": agent_id}, headers=auth_headers)
    assert rot_resp.status_code == 200
    new_cred = rot_resp.json()["credential"]
    assert new_cred != old_cred

    # Old credential is invalid
    val_old = client.post("/credentials/validate", json={"credential": old_cred, "requested_scope": "crm:read"})
    assert val_old.json()["valid"] is False

    # New credential is valid
    val_new = client.post("/credentials/validate", json={"credential": new_cred, "requested_scope": "crm:read"})
    assert val_new.json()["valid"] is True
