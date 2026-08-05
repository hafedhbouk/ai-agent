import pytest
from app.agents.schemas import AgentYAMLConfig
from app.agents.loader import AgentLoader
from app.agents.registry import AgentRegistry
from app.agents.factory import AgentFactory
from app.agents.manager import AgentManager
from app.rag.chunker import Chunker
from app.rag.schemas import DocumentMetadata, ChunkMetadata
from app.rag.ingestor import DocumentIngestor, DocumentIngestionError
from app.tools.registry import ToolRegistry
from app.tools.manager import ToolManager
from app.tools.calculator import CalculatorTool
from app.tools.base import ToolResult


def test_agent_yaml_schema_valid():
    data = {
        "name": "test_agent",
        "description": "A test agent",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 1024,
        "system_prompt": "You are a helpful assistant.",
        "vector_collection": "test_collection",
        "tools": [],
    }
    config = AgentYAMLConfig(**data)
    assert config.name == "test_agent"
    assert config.temperature == 0.7


def test_agent_yaml_schema_invalid_extra():
    data = {
        "name": "test_agent",
        "description": "A test agent",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 1024,
        "system_prompt": "You are a helpful assistant.",
        "vector_collection": "test_collection",
        "tools": [],
        "unknown_field": "should_fail",
    }
    with pytest.raises(Exception):
        AgentYAMLConfig(**data)


def test_chunker_creates_chunks():
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    text = "This is a test. " * 50
    metadata = {"source": "test.txt"}
    chunks = chunker.chunk_text(text, metadata)
    assert len(chunks) > 1
    assert all(isinstance(c, ChunkMetadata) for c in chunks)
    assert chunks[0].chunk_index == 0


def test_chunker_empty_text():
    chunker = Chunker()
    chunks = chunker.chunk_text("", {"source": "test.txt"})
    assert chunks == []


def test_ingestor_unsupported_file(tmp_path):
    ingestor = DocumentIngestor()
    file_path = tmp_path / "test.xyz"
    file_path.write_text("hello")
    with pytest.raises(DocumentIngestionError):
        import asyncio
        asyncio.run(ingestor.ingest_file(file_path, "test"))


def test_tool_manager_lists_tools():
    manager = ToolManager()
    tools = manager.list_available_tools()
    assert len(tools) >= 6
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "search" in names
    assert "rag_search" in names


def test_calculator_valid_expression():
    tool = CalculatorTool()
    result = tool.run(expression="2 + 2")
    assert result.success is True
    assert result.data["result"] == 4


def test_calculator_invalid_expression():
    tool = CalculatorTool()
    result = tool.run(expression="__import__('os').system('echo hacked')")
    assert result.success is False
