from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.core.exceptions import ToolExecutionError

logger = get_logger("tools")


class ToolInputSchema(BaseModel):
    pass


class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: type[ToolInputSchema] = ToolInputSchema
    required_permissions: List[str] = []

    def __init__(self, **kwargs):
        self.config = kwargs

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    def validate_input(self, **kwargs) -> ToolResult:
        try:
            validated = self.input_schema(**kwargs)
            return ToolResult(success=True, data=validated.model_dump())
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def execute(self, **kwargs) -> ToolResult:
        validation = self.validate_input(**kwargs)
        if not validation.success:
            return validation
        try:
            return self.run(**kwargs)
        except Exception as e:
            logger.error(f"Tool '{self.name}' execution failed: {e}")
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.model_json_schema(),
            "required_permissions": self.required_permissions,
        }
