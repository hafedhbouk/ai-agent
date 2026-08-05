from typing import List, Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry
from app.tools.rag_search import RAGSearchTool
from app.tools.sql_query import SQLQueryTool
from app.tools.send_email import SendEmailTool
from app.tools.create_pdf import CreatePDFTool
from app.tools.search import SearchTool
from app.tools.calculator import CalculatorTool
from app.core.logging import get_logger

logger = get_logger("tools.manager")


class ToolManager:
    def __init__(self):
        self.registry = ToolRegistry()
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.registry.register(RAGSearchTool)
        self.registry.register(SQLQueryTool)
        self.registry.register(SendEmailTool)
        self.registry.register(CreatePDFTool)
        self.registry.register(SearchTool)
        self.registry.register(CalculatorTool)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        tool_class = self.registry.get(name)
        if tool_class is None:
            return None
        return tool_class()

    def get_tools(self, names: List[str]) -> List[BaseTool]:
        return self.registry.get_tools(names)

    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(name)
        if tool is None:
            return ToolResult(success=False, error=f"Tool '{name}' not found")
        return tool.execute(**kwargs)

    def list_available_tools(self) -> List[Dict[str, Any]]:
        return self.registry.list_tools()

    def get_tools_for_agent(self, agent_tools: List[str]) -> List[BaseTool]:
        return self.get_tools(agent_tools)
