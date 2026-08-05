from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum as SQLEnum
import enum
from app.models.base import BaseModel


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(BaseModel):
    __tablename__ = "documents"

    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(128), nullable=True)
    collection_name = Column(String(255), index=True, nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    chunk_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
