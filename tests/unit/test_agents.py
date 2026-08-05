import pytest
import yaml
from pathlib import Path
from app.agents.schemas import AgentYAMLConfig
from app.agents.loader import AgentLoader
from app.agents.registry import AgentRegistry
from app.agents.factory import AgentFactory
from app.agents.generic import GenericAgent
from app.agents.manager import AgentManager


def test_agent_yaml_schema_valid():
    raw = {
        "name": "maintenance",
        "description": "Assistant maintenance",
        "system_prompt": "Tu es un assistant maintenance.",
        "vector_collection": "maintenance",
        "tools": ["rag_search", "sql_query"],
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 4000,
    }
    config = AgentYAMLConfig(**raw)
    assert config.name == "maintenance"
    assert config.temperature == 0.2
    assert config.max_tokens == 4000


def test_agent_yaml_schema_invalid_name():
    with pytest.raises(Exception):
        AgentYAMLConfig(
            name="invalid name!",
            description="test",
            system_prompt="test",
            vector_collection="test",
        )


def test_loader_discovers_yaml_files(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "maintenance.yaml").write_text(yaml.dump({"name": "maintenance", "description": "test", "system_prompt": "test", "vector_collection": "maintenance"}))
    (agents_dir / "commerce.yaml").write_text(yaml.dump({"name": "commerce", "description": "test", "system_prompt": "test", "vector_collection": "commerce"}))

    loader = AgentLoader(str(agents_dir))
    files = loader.discover_files()
    assert len(files) == 2


def test_loader_loads_single_config(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    yaml_content = {
        "name": "maintenance",
        "description": "Assistant maintenance",
        "system_prompt": "Tu es un assistant.",
        "vector_collection": "maintenance",
        "tools": ["rag_search"],
    }
    (agents_dir / "maintenance.yaml").write_text(yaml.dump(yaml_content))

    loader = AgentLoader(str(agents_dir))
    config = loader.load_single(agents_dir / "maintenance.yaml")
    assert config.name == "maintenance"
    assert config.tools == ["rag_search"]


def test_registry_singleton():
    r1 = AgentRegistry()
    r2 = AgentRegistry()
    assert r1 is r2


def test_factory_creates_generic_agent():
    from app.agents.schemas import AgentYAMLConfig
    config = AgentYAMLConfig(
        name="generic",
        description="Generic agent",
        system_prompt="You are helpful.",
        vector_collection="generic",
    )
    agent = AgentFactory.create(config)
    assert isinstance(agent, GenericAgent)
    assert agent.name == "generic"


def test_manager_loads_agents(tmp_path, monkeypatch):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    monkeypatch.setenv("AGENTS_DIR", str(agents_dir))
    monkeypatch.setenv("PROMPTS_DIR", str(prompts_dir))

    yaml_content = {
        "name": "maintenance",
        "description": "Assistant maintenance",
        "system_prompt": "Tu es un assistant.",
        "vector_collection": "maintenance",
    }
    (agents_dir / "maintenance.yaml").write_text(yaml.dump(yaml_content))

    from app.core.config import Settings
    from app.agents.manager import AgentManager
    from app.agents.registry import AgentRegistry

    AgentRegistry().clear()
    manager = AgentManager(agents_dir=str(agents_dir))
    configs = manager.load_agents()
    assert len(configs) == 1
    assert configs[0].name == "maintenance"
    names = [a["name"] for a in manager.list_agents()]
    assert "maintenance" in names
