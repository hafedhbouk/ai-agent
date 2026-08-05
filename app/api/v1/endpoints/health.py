from fastapi import APIRouter
from app.rag.service import RAGService
from app.agents.manager import AgentManager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("api.health")
router = APIRouter()


@router.get("/health", summary="Health check")
def health():
    agent_manager = AgentManager()
    agents = agent_manager.list_agents()
    rag_service = RAGService()
    collections = []
    try:
        import asyncio
        collections = asyncio.run(rag_service.list_collections())
    except Exception:
        collections = []
    return {
        "status": "ok",
        "version": "1.0.0",
        "agents_loaded": len(agents),
        "collections": collections,
    }
