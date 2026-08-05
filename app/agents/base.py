from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.agents.schemas import AgentYAMLConfig
from app.core.logging import get_logger

logger = get_logger("agents")


class AgentContext(BaseModel):
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, config: AgentYAMLConfig):
        self.config = config
        self.name = config.name
        self.display_name = config.name.replace("_", " ").title()
        self.description = config.description
        self.system_prompt = config.system_prompt
        self.vector_collection = config.vector_collection
        self.model_name = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.tools: List[str] = config.tools or []
        self.database_tables: List[str] = config.database_tables or []
        self.is_active = config.is_active
        logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    async def run(self, message: str, context: Optional[AgentContext] = None) -> AgentResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, message: str, context: Optional[AgentContext] = None):
        raise NotImplementedError

    def get_config(self) -> Dict[str, Any]:
        return self.config.model_dump()

    def __repr__(self) -> str:
        return f"<Agent name={self.name} model={self.model_name} tools={self.tools}>"
