from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.schemas import AgentInfo
from app.api.v1.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.services.agent_service import AgentService
from app.agents.manager import AgentManager
from app.core.logging import get_logger

logger = get_logger("api.agents")
router = APIRouter()


def get_agent_service(db: Session = Depends(get_db)) -> AgentService:
    agent_manager = AgentManager()
    agent_manager.load_agents()
    return AgentService(db, agent_manager)


@router.get("/agents", response_model=list[AgentInfo], summary="List all available agents")
def list_agents(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    return agent_service.list_agents()


@router.get("/agents/{agent_name}", response_model=AgentInfo, summary="Get agent details")
def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        return agent_service.get_agent(agent_name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/agents/reload", summary="Reload all agents from YAML files")
def reload_agents(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    names = agent_service.reload_agents()
    return {"reloaded": names}
