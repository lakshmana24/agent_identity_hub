import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.main import app
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.models.audit_log import AuditLog
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
        email="auditadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_audit_middleware_captures_post(client, auth_headers, db_session):
    payload = {
        "agent_name": "Audited Agent",
        "purpose": "Audited action",
        "department": "Security",
        "owner": "auditor@company.com",
        "requested_scopes": ["crm:read"]
    }
    response = client.post("/agents", json=payload, headers=auth_headers)
    assert response.status_code == 201

    logs = db_session.query(AuditLog).all()
    assert len(logs) >= 1
    action_names = [l.action for l in logs]
    assert "agent.register" in action_names

def test_audit_middleware_ignores_get(client, db_session):
    initial_count = db_session.query(AuditLog).count()
    response = client.get("/health")
    assert response.status_code == 200

    after_count = db_session.query(AuditLog).count()
    assert after_count == initial_count

def test_get_audit_logs_endpoint(client, auth_headers):
    # Perform a mutating action to generate an audit log
    client.post("/agents", json={
        "agent_name": "Log Viewer Agent",
        "purpose": "Generate log",
        "department": "Ops",
        "owner": "ops@company.com",
        "requested_scopes": ["crm:read"]
    }, headers=auth_headers)

    # Query GET /audit
    resp = client.get("/audit", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["logs"]) >= 1
    assert data["logs"][0]["action"] == "agent.register"
