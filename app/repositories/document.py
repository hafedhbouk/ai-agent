from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def get_by_id(self, id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_collection(self, collection_name: str, skip: int = 0, limit: int = 100):
        return (
            self.db.query(Document)
            .filter(Document.collection_name == collection_name)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, status: DocumentStatus) -> List[Document]:
        return self.db.query(Document).filter(Document.status == status).all()

    def create(self, obj_in: dict) -> Document:
        obj = Document(**obj_in)
        self.db.add(obj)
        self._commit()
        self._refresh(obj)
        return obj

    def update(self, id: int, obj_in: dict) -> Optional[Document]:
        obj = self.get_by_id(id)
        if not obj:
            return None
        for key, value in obj_in.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self._commit()
        self._refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        obj = self.get_by_id(id)
        if not obj:
            return False
        self.db.delete(obj)
        self._commit()
        return True
