# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.app import app
from app.core.dependencies import get_db
from app.models.user import User
from app.core.security import hash_password
import uuid

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} 
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#scope?function means every tests has it own database
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

#override means that the funcion that need get_db will use this one instead of the original one
@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password=hash_password("TestPass123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "TestPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(client, auth_headers):
    """Create a test project"""
    response = client.post(
        "/projects",
        json={"name": "Test Project"},
        headers=auth_headers
    )
    return response.json()