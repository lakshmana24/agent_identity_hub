import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Ensures all models are registered on Base.metadata
from app.main import app
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.models.agent import Agent
from app.models.scope_manifest import ScopeManifest
from app.auth.password import hash_password
from app.auth.jwt_handler import create_access_token
from app.repository.agent_repository import seed_default_scopes

# SQLite in-memory database with StaticPool so all connections share the same memory DB
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
        email="agentadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_list_scopes(client, auth_headers):
    response = client.get("/scopes", headers=auth_headers)
    assert response.status_code == 200
    scopes = response.json()
    assert len(scopes) >= 6
    names = [s["scope_name"] for s in scopes]
    assert "crm:read" in names
    assert "crm:write" in names

def test_register_agent_success(client, auth_headers):
    payload = {
        "agent_name": "Refund Bot",
        "purpose": "Automates customer refund processing via Stripe",
        "department": "Finance",
        "owner": "john.doe@company.com",
        "requested_scopes": ["crm:read", "tickets:read"],
        "description": "Processes refunds under $50 automatically"
    }
    response = client.post("/agents", json=payload, headers=auth_headers)
    assert response.status_code == 201
    card = response.json()
    assert card["agent_name"] == "Refund Bot"
    assert card["lifecycle_status"] == "active"
    assert card["allowed_scopes"] == ["crm:read", "tickets:read"]
    assert card["risk_level"] == "Low"

def test_register_agent_invalid_scope(client, auth_headers):
    payload = {
        "agent_name": "Rogue Bot",
        "purpose": "Invalid testing",
        "department": "IT",
        "owner": "admin@company.com",
        "requested_scopes": ["crm:read", "superadmin:all"]
    }
    response = client.post("/agents", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid scopes requested" in response.json()["detail"]

def test_get_agent_detail(client, auth_headers):
    reg_resp = client.post("/agents", json={
        "agent_name": "CRM Sync Agent",
        "purpose": "Syncs contacts",
        "department": "Sales",
        "owner": "sales.lead@company.com",
        "requested_scopes": ["crm:read", "crm:write"]
    }, headers=auth_headers)
    agent_id = reg_resp.json()["agent_id"]

    response = client.get(f"/agents/{agent_id}", headers=auth_headers)
    assert response.status_code == 200
    card = response.json()
    assert card["agent_id"] == agent_id
    assert card["risk_level"] == "Medium"  # crm:write is Medium

def test_list_agents_filtering(client, auth_headers):
    client.post("/agents", json={
        "agent_name": "Sales Agent",
        "purpose": "Sales sync",
        "department": "Sales",
        "owner": "alice@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers)

    client.post("/agents", json={
        "agent_name": "Support Agent",
        "purpose": "Support tickets",
        "department": "Support",
        "owner": "bob@company.com",
        "requested_scopes": ["tickets:read"]
    }, headers=auth_headers)

    # Filter by department=Sales
    response = client.get("/agents?department=Sales", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["agents"][0]["agent_name"] == "Sales Agent"

def test_update_agent(client, auth_headers):
    reg_resp = client.post("/agents", json={
        "agent_name": "Inventory Bot",
        "purpose": "Check stock",
        "department": "Ops",
        "owner": "ops@company.com",
        "requested_scopes": ["inventory:read"]
    }, headers=auth_headers)
    agent_id = reg_resp.json()["agent_id"]

    # Upgrade scopes to inventory:write (High risk)
    upd_resp = client.put(f"/agents/{agent_id}", json={
        "requested_scopes": ["inventory:read", "inventory:write"]
    }, headers=auth_headers)
    assert upd_resp.status_code == 200
    card = upd_resp.json()
    assert "inventory:write" in card["allowed_scopes"]
    assert card["risk_level"] == "High"

def test_soft_delete_agent(client, auth_headers):
    reg_resp = client.post("/agents", json={
        "agent_name": "Old Bot",
        "purpose": "Deprecated",
        "department": "IT",
        "owner": "admin@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers)
    agent_id = reg_resp.json()["agent_id"]

    del_resp = client.delete(f"/agents/{agent_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deprovisioned"

    # Default list excludes deprovisioned
    list_resp = client.get("/agents", headers=auth_headers)
    assert list_resp.json()["total"] == 0

    # Filter with status=deprovisioned shows it
    list_dep_resp = client.get("/agents?status=deprovisioned", headers=auth_headers)
    assert list_dep_resp.json()["total"] == 1
