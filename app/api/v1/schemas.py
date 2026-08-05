from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    agent_name: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    model: Optional[str] = None


class DocumentUploadRequest(BaseModel):
    collection_name: str = Field(..., min_length=1)
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)


class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    model: str
    temperature: float
    tools: List[str]
    is_active: bool
    vector_collection: str


class HealthResponse(BaseModel):
    status: str
    version: str
    agents_loaded: int
    collections: List[str]
