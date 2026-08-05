import threading
from typing import Dict, Optional, List, Any
from app.agents.base import BaseAgent
from app.agents.schemas import AgentYAMLConfig
from app.core.logging import get_logger
from app.core.exceptions import AgentPlatformException

logger = get_logger("agents.registry")


class AgentRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._agents: Dict[str, BaseAgent] = {}
                    cls._instance._configs: Dict[str, AgentYAMLConfig] = {}
        return cls._instance

    def register(self, agent: BaseAgent, config: AgentYAMLConfig) -> None:
        self._agents[agent.name] = agent
        self._configs[agent.name] = config
        logger.info(f"Registered agent: {agent.name}")

    def unregister(self, name: str) -> bool:
        if name in self._agents:
            del self._agents[name]
            self._configs.pop(name, None)
            logger.info(f"Unregistered agent: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_config(self, name: str) -> Optional[AgentYAMLConfig]:
        return self._configs.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        result = []
        for name, agent in self._agents.items():
            config = self._configs.get(name)
            result.append({
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "model": agent.model_name,
                "temperature": agent.temperature,
                "tools": [t.name for t in agent.tools] if agent.tools else [],
                "is_active": agent.is_active,
                "vector_collection": agent.vector_collection,
                "config_path": config.config_path if config else None,
            })
        return result

    def list_names(self) -> List[str]:
        return list(self._agents.keys())

    def clear(self) -> None:
        self._agents.clear()
        self._configs.clear()
        logger.info("Agent registry cleared")
