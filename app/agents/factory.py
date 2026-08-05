from typing import Type, Dict, Any
from app.agents.base import BaseAgent, AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.agents.registry import AgentRegistry
from app.core.logging import get_logger

logger = get_logger("agents.factory")


class AgentFactory:
    _builders: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register_builder(cls, agent_type: str, builder: Type[BaseAgent]) -> None:
        cls._builders[agent_type] = builder
        logger.debug(f"Registered builder for agent type: {agent_type}")

    @classmethod
    def create(cls, config: AgentYAMLConfig, **kwargs) -> BaseAgent:
        agent_type = config.name
        builder = cls._builders.get(agent_type)
        if builder is None:
            from app.agents.generic import GenericAgent
            logger.warning(f"No specific builder for '{agent_type}', using GenericAgent")
            builder = GenericAgent
        agent = builder(config, **kwargs)
        return agent

    @classmethod
    def load_and_register(cls, config: AgentYAMLConfig, **kwargs) -> BaseAgent:
        agent = cls.create(config, **kwargs)
        registry = AgentRegistry()
        registry.register(agent, config)
        return agent
