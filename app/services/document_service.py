from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.rag.service import RAGService
from app.core.logging import get_logger

logger = get_logger("services.document")


class DocumentService:
    def __init__(self, db: Session, rag_service: RAGService):
        self.db = db
        self.rag_service = rag_service

    async def ingest_file(self, user_id: Optional[int], file_path: str, collection_name: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Dict[str, Any]:
        doc = Document(
            filename=file_path.split("/")[-1],
            file_path=file_path,
            collection_name=collection_name,
            status=DocumentStatus.PROCESSING,
            uploaded_by=user_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        try:
            chunk_ids = await self.rag_service.ingest_file(file_path, collection_name, chunk_size, chunk_overlap)
            doc.status = DocumentStatus.INDEXED
            doc.chunk_count = len(chunk_ids)
            self.db.commit()
            logger.info(f"Document {doc.id} indexed successfully")
            return {"document_id": doc.id, "chunks_created": len(chunk_ids), "status": "indexed"}
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            self.db.commit()
            logger.error(f"Document {doc.id} ingestion failed: {e}")
            return {"document_id": doc.id, "status": "failed", "error": str(e)}

    def get_documents(self, collection_name: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Document]:
        query = self.db.query(Document)
        if collection_name:
            query = query.filter(Document.collection_name == collection_name)
        return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def get_document(self, document_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def delete_document(self, document_id: int) -> bool:
        doc = self.get_document(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True
