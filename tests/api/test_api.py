import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"
os.environ["OPENAI_API_KEY"] = "sk-test"

from app.models.base import Base
from app.models.user import User
from app.database.session import engine
from app.api.v1.app import app
from app.utils.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.database.session import get_db
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    if not db.query(User).filter(User.email == "test@example.com").first():
        user = User(email="test@example.com", hashed_password="$2b$12$OzX1.pxoeC7RoXgzdubeIuvdTt.2QXrFzs8v0y.ef.nRV98LgquaO", full_name="Test User")
        db.add(user)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "agents_loaded" in data


def test_login_endpoint():
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_list_agents_unauthorized():
    response = client.get("/api/v1/agents")
    assert response.status_code == 401


def test_list_agents_authorized():
    login = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "testpass"})
    token = login.json()["access_token"]
    response = client.get("/api/v1/agents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
