from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.rag_search")


class RAGSearchInput(ToolInputSchema):
    query: str
    collection_name: str
    top_k: int = 5


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "Search in a vector collection using semantic search"
    input_schema = RAGSearchInput
    required_permissions = ["rag:read"]

    def __init__(self, rag_service: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.rag_service = rag_service

    def run(self, query: str, collection_name: str, top_k: int = 5) -> ToolResult:
        if self.rag_service is None:
            try:
                from app.rag.service import RAGService
                self.rag_service = RAGService()
            except Exception as e:
                return ToolResult(success=False, error=f"RAG service unavailable: {e}")
        try:
            import asyncio
            result = asyncio.run(self.rag_service.search(query, collection_name, top_k))
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return ToolResult(success=False, error=str(e))
