from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, MessageRole
from app.models.agent import Agent as AgentModel
from app.models.user import User
from app.agents.manager import AgentManager, AgentNotFoundError
from app.agents.base import AgentContext, AgentResponse
from app.rag.service import RAGService
from app.tools.manager import ToolManager
from app.core.logging import get_logger
from app.core.exceptions import AgentPlatformException

logger = get_logger("services.chat")


class ChatService:
    def __init__(self, db: Session, agent_manager: AgentManager, rag_service: RAGService, tool_manager: ToolManager):
        self.db = db
        self.agent_manager = agent_manager
        self.rag_service = rag_service
        self.tool_manager = tool_manager

    async def chat(self, user: Optional[User], request: Any) -> Dict[str, Any]:
        agent = self.agent_manager.get_agent(request.agent_name)
        conversation = self._get_or_create_conversation(user, request.agent_name, request.conversation_id)
        history = self._get_history(conversation.id)
        rag_context = await self._get_rag_context(request.message, agent.vector_collection)
        metadata: Dict[str, Any] = {"history": history}
        if rag_context:
            metadata["rag_context"] = rag_context
        agent_context = AgentContext(
            conversation_id=conversation.id,
            user_id=user.id if user else None,
            metadata=metadata,
        )
        response: AgentResponse = await self.agent_manager.run_agent(request.agent_name, request.message, agent_context)
        user_msg = Message(conversation_id=conversation.id, role=MessageRole.USER, content=request.message)
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response.content,
            sources=response.sources or [],
            tokens_used=response.tokens_used,
            latency_ms=response.latency_ms,
            model=response.model,
        )
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        return {
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "content": response.content,
            "sources": response.sources or [],
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms,
            "model": response.model,
        }

    def _get_or_create_conversation(self, user: Optional[User], agent_name: str, conversation_id: Optional[int]) -> Conversation:
        if conversation_id:
            conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                return conv
        conv = Conversation(title=None, agent_name=agent_name, user_id=user.id if user else None)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def _get_history(self, conversation_id: int, max_messages: int = 20) -> List[Dict[str, str]]:
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_messages)
            .all()
        )
        return [{"role": m.role.value, "content": m.content} for m in reversed(messages)]

    async def _get_rag_context(self, query: str, collection_name: Optional[str], top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        if not collection_name:
            return None
        try:
            result = await self.rag_service.search(query=query, collection_name=collection_name, top_k=top_k)
            return result.get("results") or result.get("documents") or []
        except Exception as e:
            logger.warning(f"RAG search failed for collection '{collection_name}': {e}")
            return None
