import pytest
from app.tools.calculator import CalculatorTool, CalculatorInput
from app.tools.search import SearchTool, SearchInput
from app.tools.registry import ToolRegistry
from app.tools.manager import ToolManager
from app.tools.base import ToolResult


def test_calculator_valid_expression():
    tool = CalculatorTool()
    result = tool.run(expression="2 + 2")
    assert result.success is True
    assert result.data["result"] == 4


def test_calculator_invalid_expression():
    tool = CalculatorTool()
    result = tool.run(expression="__import__('os').system('echo hacked')")
    assert result.success is False
    assert "not allowed" in result.error


def test_search_tool_schema():
    tool = SearchTool()
    schema = tool.get_schema()
    assert schema["name"] == "search"
    assert "input_schema" in schema


def test_tool_registry_singleton():
    r1 = ToolRegistry()
    r2 = ToolRegistry()
    assert r1 is r2


def test_tool_manager_lists_tools():
    manager = ToolManager()
    tools = manager.list_available_tools()
    assert len(tools) >= 6
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "search" in names
    assert "rag_search" in names


def test_tool_manager_get_tools_for_agent():
    manager = ToolManager()
    tools = manager.get_tools_for_agent(["calculator", "search"])
    assert len(tools) == 2
    assert tools[0].name == "calculator"
    assert tools[1].name == "search"
