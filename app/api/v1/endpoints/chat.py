from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.api.v1.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.services.chat_service import ChatService
from app.agents.manager import AgentManager
from app.rag.service import RAGService
from app.tools.manager import ToolManager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("api.chat")
router = APIRouter()


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    agent_manager = AgentManager()
    agent_manager.load_agents()
    rag_service = RAGService()
    tool_manager = ToolManager()
    return ChatService(db, agent_manager, rag_service, tool_manager)


@router.post("/chat", response_model=ChatResponse, summary="Send a message to an agent")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        result = await chat_service.chat(current_user, request)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
