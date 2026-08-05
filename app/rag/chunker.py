from typing import List, Dict, Any, Optional
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.schemas import DocumentMetadata, ChunkMetadata
from app.core.logging import get_logger

logger = get_logger("rag.chunker")


class ChunkingStrategy:
    RECURSIVE = "recursive"
    MARKDOWN = "markdown"
    FIXED = "fixed"


class Chunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: str = ChunkingStrategy.RECURSIVE,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self._splitter = self._create_splitter()

    def _create_splitter(self) -> RecursiveCharacterTextSplitter:
        if self.strategy == ChunkingStrategy.MARKDOWN:
            return RecursiveCharacterTextSplitter.from_language(
                language="markdown",
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[ChunkMetadata]:
        if not text or not text.strip():
            return []
        chunks = self._splitter.split_text(text)
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = hashlib.md5(f"{metadata.get('source', '')}_{i}_{chunk_text[:100]}".encode()).hexdigest()
            chunk_meta = ChunkMetadata(
                chunk_id=chunk_id,
                text=chunk_text,
                chunk_index=i,
                total_chunks=len(chunks),
                source=metadata.get("source", ""),
                document_id=metadata.get("document_id"),
                metadata=metadata,
            )
            result.append(chunk_meta)
        logger.debug(f"Chunked text into {len(result)} chunks")
        return result

    def chunk_documents(self, documents: List[DocumentMetadata]) -> List[ChunkMetadata]:
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(doc.content, doc.metadata)
            all_chunks.extend(chunks)
        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
