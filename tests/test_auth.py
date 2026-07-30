import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.models.admin import Admin
from app.auth.password import hash_password

# Use SQLite in-memory database for fast, isolated unit tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
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
def test_admin(db_session):
    admin = Admin(
        email="testadmin@example.com",
        hashed_password=hash_password("Password123!"),
        role="superadmin",
        org_id="org_test"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

def test_login_success(client, test_admin):
    response = client.post("/auth/login", json={
        "email": "testadmin@example.com",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_admin):
    response = client.post("/auth/login", json={
        "email": "testadmin@example.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_nonexistent_email(client, test_admin):
    response = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "Password123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_get_me_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_get_me_success(client, test_admin):
    login_resp = client.post("/auth/login", json={
        "email": "testadmin@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testadmin@example.com"
    assert data["role"] == "superadmin"

def test_refresh_token(client, test_admin):
    login_resp = client.post("/auth/login", json={
        "email": "testadmin@example.com",
        "password": "Password123!"
    })
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post("/auth/refresh-token", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
