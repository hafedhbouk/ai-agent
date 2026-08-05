from typing import Optional
from app.rag.retriever import RAGRetriever
from app.rag.chunker import Chunker, ChunkingStrategy
from app.rag.ingestor import DocumentIngestor
from app.vectorstore.chromadb import ChromaDBVectorStore
from app.vectorstore.base import BaseVectorStore
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("rag.service")


class RAGService:
    def __init__(self, vector_store: Optional[BaseVectorStore] = None):
        self.vector_store = vector_store or ChromaDBVectorStore()
        self.chunker = Chunker()
        self.ingestor = DocumentIngestor()
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            chunker=self.chunker,
            ingestor=self.ingestor,
        )

    async def ingest_file(
        self,
        file_path: str,
        collection_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list:
        return await self.retriever.ingest_document(file_path, collection_name, chunk_size, chunk_overlap)

    async def search(self, query: str, collection_name: str, top_k: int = 5) -> dict:
        result = await self.retriever.search(query, collection_name, top_k)
        return result.model_dump()

    async def delete_collection(self, collection_name: str) -> bool:
        return await self.retriever.delete_collection(collection_name)

    async def list_collections(self) -> list:
        return await self.retriever.list_collections()

    async def get_collection_stats(self, collection_name: str) -> dict:
        return await self.retriever.get_collection_stats(collection_name)
