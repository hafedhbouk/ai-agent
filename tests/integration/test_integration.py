import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_integration.db"
os.environ["OPENAI_API_KEY"] = "sk-test"

from app.models.base import Base
from app.models.user import User
from app.database.session import get_db
from app.api.v1.app import app
from app.utils.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    if not db.query(User).filter(User.email == "integration@test.com").first():
        user = User(
            email="integration@test.com",
            hashed_password="$2b$12$OzX1.pxoeC7RoXgzdubeIuvdTt.2QXrFzs8v0y.ef.nRV98LgquaO",
            full_name="Integration Test User",
        )
        db.add(user)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


def get_token(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "integration@test.com", "password": "testpass"},
    )
    return response.json()["access_token"]


from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage


def fake_llm(*args, **kwargs):
    return AIMessage(content="Mocked agent response")


class TestIntegrationChat:
    @patch("app.llm.providers.LLMProviderFactory.create", lambda *args, **kwargs: RunnableLambda(fake_llm))
    def test_chat_endpoint_returns_response(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/v1/chat",
            headers=headers,
            json={"message": "Hello", "agent_name": "maintenance", "conversation_id": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "conversation_id" in data

    @patch("app.llm.providers.LLMProviderFactory.create", lambda *args, **kwargs: RunnableLambda(fake_llm))
    def test_chat_with_unknown_agent(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/v1/chat",
            headers=headers,
            json={"message": "Hello", "agent_name": "nonexistent_agent", "conversation_id": None},
        )
        assert response.status_code == 404


class TestIntegrationAgents:
    def test_list_agents_returns_all(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/agents", headers=headers)
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) >= 4

    def test_reload_agents(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/agents/reload", headers=headers)
        assert response.status_code == 200


class TestIntegrationDocuments:
    def test_upload_endpoint_requires_auth(self, client):
        response = client.post("/api/v1/documents/upload")
        assert response.status_code == 401

    def test_documents_list_requires_auth(self, client):
        response = client.get("/api/v1/documents")
        assert response.status_code == 401


class TestIntegrationWorkflows:
    def test_list_workflows(self, client):
        response = client.get("/api/v1/workflows/")
        assert response.status_code == 200
        workflows = response.json()
        assert isinstance(workflows, list)

    def test_register_workflow(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        workflow_def = {
            "workflow_id": "test_workflow",
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "step1",
                    "step_type": "agent",
                    "agent_name": "maintenance",
                    "parameters": {},
                }
            ],
        }
        response = client.post(
            "/api/v1/workflows/",
            headers=headers,
            json=workflow_def,
        )
        assert response.status_code == 200

    def test_trigger_workflow(self, client):
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/v1/workflows/trigger/test_workflow",
            headers=headers,
            json={"message": "Test trigger"},
        )
        assert response.status_code == 200


class TestIntegrationHealth:
    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "agents_loaded" in data


class TestIntegrationAuth:
    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_login_valid_credentials(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "integration@test.com", "password": "testpass"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestIntegrationTools:
    def test_calculator_tool(self):
        from app.tools.calculator import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(expression="10 + 5")
        assert result.success is True
        assert result.data["result"] == 15

    def test_calculator_tool_invalid(self):
        from app.tools.calculator import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(expression="__import__('os')")
        assert result.success is False

    def test_tool_manager_lists_all_tools(self):
        from app.tools.manager import ToolManager
        tm = ToolManager()
        tools = tm.list_available_tools()
        tool_names = [t["name"] for t in tools]
        assert "calculator" in tool_names
        assert "ocr" in tool_names
        assert "web_scraper" in tool_names
        assert "rag_search" in tool_names
        assert "sql_query" in tool_names
        assert "send_email" in tool_names
        assert "create_pdf" in tool_names
        assert "search" in tool_names
