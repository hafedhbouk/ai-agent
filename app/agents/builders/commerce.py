from typing import Optional, List, Any
from app.agents.generic import GenericAgent
from app.agents.base import AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.core.logging import get_logger

logger = get_logger("agents.builders.commerce")


class CommerceAgent(GenericAgent):
    def __init__(self, config: AgentYAMLConfig, tools: Optional[List[Any]] = None, **kwargs):
        super().__init__(config, tools=tools, **kwargs)
        self.display_name = config.name.replace("_", " ").title()
        self.description = config.description

    async def run(self, message: str, context: Optional[AgentContext] = None) -> AgentResponse:
        logger.info(f"Running commerce agent with message: {message[:100]}")
        return await super().run(message, context)

    async def stream(self, message: str, context: Optional[AgentContext] = None):
        logger.info(f"Streaming commerce agent with message: {message[:100]}")
        async for chunk in super().stream(message, context):
            yield chunk
