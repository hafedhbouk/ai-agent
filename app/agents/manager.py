from typing import Optional, List, Dict, Any
from app.agents.base import BaseAgent, AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.agents.loader import AgentLoader
from app.agents.registry import AgentRegistry
from app.agents.factory import AgentFactory
from app.core.logging import get_logger
from app.core.config import settings
from app.core.exceptions import AgentPlatformException

logger = get_logger("agents.manager")


class AgentNotFoundError(AgentPlatformException):
    def __init__(self, agent_name: str):
        super().__init__(f"Agent '{agent_name}' not found", "AGENT_NOT_FOUND")


class AgentManager:
    def __init__(self, agents_dir: Optional[str] = None):
        self.loader = AgentLoader(agents_dir or settings.agents_dir)
        self.registry = AgentRegistry()
        self._loaded = False

    def load_agents(self) -> List[AgentYAMLConfig]:
        configs = self.loader.load_all()
        loaded = []
        for config in configs:
            try:
                agent = AgentFactory.load_and_register(config)
                loaded.append(config)
            except Exception as e:
                logger.error(f"Failed to register agent '{config.name}': {e}")
        self._loaded = True
        return loaded

    def get_agent(self, name: str) -> BaseAgent:
        if not self._loaded:
            self.load_agents()
        agent = self.registry.get(name)
        if agent is None:
            raise AgentNotFoundError(name)
        return agent

    def list_agents(self) -> List[Dict[str, Any]]:
        if not self._loaded:
            self.load_agents()
        return self.registry.list_agents()

    def reload(self) -> List[AgentYAMLConfig]:
        self.registry.clear()
        self._loaded = False
        return self.load_agents()

    def get_agent_names(self) -> List[str]:
        if not self._loaded:
            self.load_agents()
        return self.registry.list_names()

    async def run_agent(self, name: str, message: str, context: Optional[AgentContext] = None) -> AgentResponse:
        agent = self.get_agent(name)
        logger.info(f"Running agent '{name}' with message length {len(message)}")
        return await agent.run(message, context)
