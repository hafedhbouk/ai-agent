from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("vectorstore")


class DocumentChunk(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseVectorStore(ABC):
    @abstractmethod
    async def add_documents(self, chunks: List[DocumentChunk], collection_name: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_collections(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        raise NotImplementedError
