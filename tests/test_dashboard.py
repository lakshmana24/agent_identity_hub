import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.main import app
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

@pytest.fixture
def auth_headers(db_session):
    admin = Admin(
        email="dashadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_get_dashboard_metrics(client, auth_headers):
    # 1. Register a Low risk agent
    reg1 = client.post("/agents", json={
        "agent_name": "Dash Low Risk Bot",
        "purpose": "General support queries",
        "department": "Support",
        "owner": "support@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers).json()

    # 2. Register a High risk agent
    client.post("/agents", json={
        "agent_name": "Dash High Risk Bot",
        "purpose": "Process refunds via Stripe",
        "department": "Finance",
        "owner": "finance@company.com",
        "requested_scopes": ["crm:read", "inventory:write"]
    }, headers=auth_headers)

    # 3. Generate credential for agent 1
    client.post("/credentials/generate", json={"agent_id": reg1["agent_id"]}, headers=auth_headers)

    # 4. Call GET /dashboard
    resp = client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_agents"] >= 2
    assert data["active_agents"] >= 2
    assert data["risk_distribution"]["Low"] >= 1
    assert data["risk_distribution"]["High"] >= 1
    assert data["average_security_score"] > 0
    assert len(data["recent_audit_activity"]) >= 1
