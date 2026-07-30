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
from app.models.scope_manifest import ScopeManifest
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

    import app.middleware.audit_middleware as am
    def _override_session_local():
        return db_session

    original_session_local = am.SessionLocal
    am.SessionLocal = _override_session_local

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    am.SessionLocal = original_session_local

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

def test_create_agent_with_ai_metadata(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="creator@example.com")
    payload = {
        "agent_name": "FrontierCodeAgent",
        "model_provider": "Anthropic",
        "model_name": "claude-3-5-sonnet",
        "tools": ["web_search", "code_execution"],
        "purpose": "Monitors server logs and executes automated shell fixes",
        "department": "DevOps",
        "owner": "devops@company.com",
        "requested_scopes": ["tickets:read", "inventory:write"]
    }
    resp = client.post("/agents", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_provider"] == "Anthropic"
    assert data["model_name"] == "claude-3-5-sonnet"
    assert "code_execution" in data["tools"]
    assert data["ai_summary"] is not None

def test_runtime_scope_management(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="scopemgr@example.com")
    
    # 1. Create scope
    new_scope = {
        "scope_name": "custom:execute",
        "action_type": "write",
        "description": "Execute custom remote automation jobs",
        "risk_level": "High"
    }
    resp = client.post("/scopes", json=new_scope, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["scope_name"] == "custom:execute"

    # 2. List scopes
    list_resp = client.get("/scopes", headers=headers)
    assert list_resp.status_code == 200
    names = [s["scope_name"] for s in list_resp.json()]
    assert "custom:execute" in names

    # 3. Delete scope
    del_resp = client.delete("/scopes/custom:execute", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

def test_admin_rbac_roles(client, db_session):
    super_headers = get_auth_headers(db_session, role="superadmin", email="super1@example.com")
    auditor_headers = get_auth_headers(db_session, role="auditor", email="auditor1@example.com")

    # Superadmin creates an admin
    resp = client.post("/admins", json={
        "email": "newoperator@example.com",
        "password": "OperatorPass123!",
        "role": "admin"
    }, headers=super_headers)
    assert resp.status_code == 201

    # Auditor GETs agents -> Allowed
    get_resp = client.get("/agents", headers=auditor_headers)
    assert get_resp.status_code == 200

    # Auditor POSTs agent -> Forbidden 403
    post_resp = client.post("/agents", json={
        "agent_name": "AuditorBot",
        "purpose": "Forbidden test",
        "department": "Audit",
        "owner": "auditor@example.com",
        "requested_scopes": ["crm:read"]
    }, headers=auditor_headers)
    assert post_resp.status_code == 403

def test_explicit_expires_at_testing_override(client, db_session):
    headers = get_auth_headers(db_session, role="superadmin", email="expirytester@example.com")
    reg = client.post("/agents", json={
        "agent_name": "TestingOverrideBot",
        "purpose": "Test explicit expires_at override",
        "department": "QA",
        "owner": "qa@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=headers).json()
    agent_id = reg["agent_id"]

    # Generate credential with explicit past expires_at timestamp
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    gen = client.post("/credentials/generate", json={
        "agent_id": agent_id,
        "expires_at": past_iso
    }, headers=headers).json()
    raw_cred = gen["credential"]

    # Validate credential immediately -> Should be rejected as expired
    val_resp = client.post("/credentials/validate", json={
        "credential": raw_cred,
        "requested_scope": "crm:read"
    })
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["valid"] is False
    assert val_data["reason"] == "expired"

def test_ai_status_and_health_head(client):
    status_resp = client.get("/ai/status")
    assert status_resp.status_code == 200
    assert "ai_mode" in status_resp.json()

    head_resp = client.head("/health")
    assert head_resp.status_code == 200
