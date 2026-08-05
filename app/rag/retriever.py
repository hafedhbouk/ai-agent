from typing import List, Optional, Dict, Any
from app.rag.schemas import RetrievalResult
from app.rag.chunker import Chunker
from app.rag.ingestor import DocumentIngestor
from app.vectorstore.base import BaseVectorStore
from app.core.logging import get_logger

logger = get_logger("rag.retriever")


class RAGRetriever:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        chunker: Optional[Chunker] = None,
        ingestor: Optional[DocumentIngestor] = None,
    ):
        self.vector_store = vector_store
        self.chunker = chunker or Chunker()
        self.ingestor = ingestor or DocumentIngestor()

    async def ingest_document(
        self,
        file_path: str,
        collection_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[str]:
        path = Path(file_path)
        doc_meta = await self.ingestor.ingest_file(path, collection_name)
        self.chunker.chunk_size = chunk_size
        self.chunker.chunk_overlap = chunk_overlap
        chunks = self.chunker.chunk_documents([doc_meta])
        if not chunks:
            return []
        from app.vectorstore.base import DocumentChunk
        vector_chunks = [
            DocumentChunk(text=c.text, metadata=c.metadata, id=c.chunk_id) for c in chunks
        ]
        ids = await self.vector_store.add_documents(vector_chunks, collection_name)
        logger.info(f"Ingested {len(ids)} chunks from {path.name} into '{collection_name}'")
        return ids

    async def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        import time
        start = time.time()
        results = await self.vector_store.search(query, collection_name, top_k, filter_metadata)
        latency = int((time.time() - start) * 1000)
        chunks = [{"text": r.chunk.text, "score": r.score, "metadata": r.metadata} for r in results]
        logger.info(f"Retrieved {len(chunks)} chunks for query in '{collection_name}'")
        return RetrievalResult(
            query=query,
            collection_name=collection_name,
            chunks=chunks,
            total_chunks_found=len(chunks),
            latency_ms=latency,
        )

    async def delete_collection(self, collection_name: str) -> bool:
        return await self.vector_store.delete_collection(collection_name)

    async def list_collections(self) -> List[str]:
        return await self.vector_store.list_collections()

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        return await self.vector_store.get_collection_stats(collection_name)
