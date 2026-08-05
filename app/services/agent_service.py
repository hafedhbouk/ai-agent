from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.agent import Agent as AgentModel
from app.agents.manager import AgentManager
from app.core.logging import get_logger

logger = get_logger("services.agent")


class AgentService:
    def __init__(self, db: Session, agent_manager: AgentManager):
        self.db = db
        self.agent_manager = agent_manager

    def list_agents(self) -> List[Dict[str, Any]]:
        return self.agent_manager.list_agents()

    def get_agent(self, name: str) -> Dict[str, Any]:
        agents = self.agent_manager.list_agents()
        for agent in agents:
            if agent["name"] == name:
                return agent
        from app.core.exceptions import AgentNotFoundError
        raise AgentNotFoundError(name)

    def reload_agents(self) -> List[str]:
        configs = self.agent_manager.reload()
        return [c.name for c in configs]
