from typing import Type, Dict, Any, Optional, List
from app.agents.base import BaseAgent, AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.agents.registry import AgentRegistry
from app.agents.generic import GenericAgent
from app.agents.langgraph.orchestrator import orchestrator
from app.agents.builders.commerce import CommerceAgent
from app.agents.builders.maintenance import MaintenanceAgent
from app.core.logging import get_logger

logger = get_logger("agents.factory")


class AgentFactory:
    _builders: Dict[str, Type[BaseAgent]] = {
        "commerce": CommerceAgent,
        "maintenance": MaintenanceAgent,
    }

    @classmethod
    def register_builder(cls, agent_type: str, builder: Type[BaseAgent]) -> None:
        cls._builders[agent_type] = builder
        logger.debug(f"Registered builder for agent type: {agent_type}")

    @classmethod
    def create(cls, config: AgentYAMLConfig, tools: Optional[List[Any]] = None, **kwargs) -> BaseAgent:
        agent_type = config.name
        builder = cls._builders.get(agent_type)
        if builder is None:
            logger.warning(f"No specific builder for '{agent_type}', using GenericAgent")
            builder = GenericAgent
        agent = builder(config, tools=tools, **kwargs)
        return agent

    @classmethod
    def load_and_register(cls, config: AgentYAMLConfig, tools: Optional[List[Any]] = None, **kwargs) -> BaseAgent:
        agent = cls.create(config, tools=tools, **kwargs)
        registry = AgentRegistry()
        registry.register(agent, config)
        return agent
