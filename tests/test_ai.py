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
from app.ai.gemini_client import LiveGeminiClient, MockAIClient

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
        email="aiadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token({"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.org_id})
    return {"Authorization": f"Bearer {token}"}

def test_scope_recommendation_refunds(client, auth_headers):
    payload = {"purpose": "Automates customer refund processing via Stripe"}
    resp = client.post("/governance/scope-recommendation", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "crm:read" in data["recommended_scopes"]
    assert "payments:write" in data["rejected_scopes"]
    assert data["risk_level"] == "High"
    assert "financial" in data["reasoning"].lower()

def test_scope_recommendation_support(client, auth_headers):
    payload = {"purpose": "Answers customer support tickets and manages queries"}
    resp = client.post("/governance/scope-recommendation", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tickets:read" in data["recommended_scopes"]
    assert "tickets:write" in data["recommended_scopes"]
    assert data["risk_level"] == "Medium"

def test_generate_identity_summary(client, auth_headers):
    payload = {
        "agent_name": "Refund Bot",
        "purpose": "Automates customer refund processing via Stripe",
        "department": "Finance",
        "scopes": ["crm:read", "tickets:read"],
        "risk_level": "High"
    }
    resp = client.post("/governance/identity-summary", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "Refund Bot" in data["summary"]
    assert "Finance" in data["summary"]

def test_fallback_on_malformed_ai_response():
    # Pass bogus API key to LiveGeminiClient -> should fall back gracefully to mock
    client = LiveGeminiClient(api_key="invalid_fake_api_key")
    res = client.recommend_scopes(purpose="refund processing", available_scopes=["crm:read", "payments:write"])
    assert res.risk_level == "High"
    assert "payments:write" in res.rejected_scopes
