from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    source: str
    content: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkMetadata(BaseModel):
    chunk_id: str
    text: str
    chunk_index: int
    total_chunks: int
    source: str
    document_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    document_id: int
    filename: str
    collection_name: str
    chunks_created: int
    status: str
    error: Optional[str] = None


class RetrievalResult(BaseModel):
    query: str
    collection_name: str
    chunks: List[Dict[str, Any]]
    total_chunks_found: int
    latency_ms: Optional[int] = None
