from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.api.v1.schemas import DocumentUploadRequest
from app.api.v1.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.services.document_service import DocumentService
from app.rag.service import RAGService
from app.core.logging import get_logger
import aiofiles
import os
from pathlib import Path

logger = get_logger("api.documents")
router = APIRouter()


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    rag_service = RAGService()
    return DocumentService(db, rag_service)


@router.post("/upload", summary="Upload a document for ingestion")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "default",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        result = await document_service.ingest_file(current_user.id, str(file_path), collection_name, chunk_size, chunk_overlap)
        return result
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/documents", summary="List ingested documents")
def list_documents(
    collection_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    docs = document_service.get_documents(collection_name, skip, limit)
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "collection_name": d.collection_name,
            "status": d.status.value,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]
