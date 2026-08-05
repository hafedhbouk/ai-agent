from typing import List, Dict, Any, Optional
import os
from app.vectorstore.base import BaseVectorStore, DocumentChunk, SearchResult
from app.core.logging import get_logger
from app.core.exceptions import VectorStoreError
from app.core.config import settings

logger = get_logger("vectorstore.chroma")


class ChromaDBVectorStore(BaseVectorStore):
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.chroma_db_path
        self._client = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            os.makedirs(self.persist_directory, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._initialized = True
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
        except ImportError:
            raise VectorStoreError("chromadb is not installed. Install it or use a different vector store.")
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB: {e}")

    async def add_documents(self, chunks: List[DocumentChunk], collection_name: str) -> List[str]:
        await self._ensure_initialized()
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            embedding_fn = OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model,
            )
            collection = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            ids = []
            documents = []
            metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_id = chunk.id or f"{collection_name}_{i}"
                ids.append(chunk_id)
                documents.append(chunk.text)
                meta = dict(chunk.metadata)
                meta["chunk_id"] = chunk_id
                metadatas.append(meta)
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"Added {len(chunks)} chunks to collection '{collection_name}'")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise VectorStoreError(str(e))

    async def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        await self._ensure_initialized()
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            embedding_fn = OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model,
            )
            collection = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
            )
            where = filter_metadata if filter_metadata else None
            results = collection.query(query_texts=[query], n_results=top_k, where=where)
            search_results = []
            if results and results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    chunk = DocumentChunk(text=doc, metadata=metadata)
                    search_results.append(SearchResult(chunk=chunk, score=1.0 - distance, metadata=metadata))
            logger.info(f"Search in '{collection_name}' returned {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            raise VectorStoreError(str(e))

    async def delete_collection(self, collection_name: str) -> bool:
        await self._ensure_initialized()
        try:
            self._client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception:
            return False

    async def list_collections(self) -> List[str]:
        await self._ensure_initialized()
        try:
            collections = self._client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        await self._ensure_initialized()
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            embedding_fn = OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model,
            )
            collection = self._client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)
            count = collection.count()
            return {"name": collection_name, "count": count}
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"name": collection_name, "count": 0}
