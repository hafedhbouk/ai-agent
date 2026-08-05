from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def get_by_id(self, id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> User:
        obj = User(**obj_in)
        self.db.add(obj)
        self._commit()
        self._refresh(obj)
        return obj

    def update(self, id: int, obj_in: dict) -> Optional[User]:
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
