from typing import Dict, Type, List, Optional, Any
from app.tools.base import BaseTool, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.registry")


class ToolRegistry:
    _instance = None
    _tools: Dict[str, Type[BaseTool]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool_class: Type[BaseTool]) -> None:
        instance = tool_class() if not isinstance(tool_class, type) else tool_class()
        self._tools[instance.name] = tool_class
        logger.info(f"Tool registered: {instance.name}")

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Tool unregistered: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[Type[BaseTool]]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        result = []
        for name, tool_class in self._tools.items():
            instance = tool_class() if not isinstance(tool_class, type) else tool_class()
            result.append(instance.get_schema())
        return result

    def get_tools(self, names: List[str]) -> List[BaseTool]:
        tools = []
        for name in names:
            tool_class = self._tools.get(name)
            if tool_class:
                tools.append(tool_class() if not isinstance(tool_class, type) else tool_class())
        return tools

    def clear(self) -> None:
        self._tools.clear()
        logger.info("Tool registry cleared")
