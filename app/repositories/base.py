from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.core.exceptions import AgentPlatformException

ModelType = TypeVar("ModelType")
logger = get_logger("repository")


class BaseRepository(ABC, Generic[ModelType]):
    model: Type[ModelType] = None

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int) -> bool:
        raise NotImplementedError

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database commit error: {e}")
            raise AgentPlatformException(f"Database error: {str(e)}", "DATABASE_ERROR")

    def _refresh(self, obj: ModelType) -> ModelType:
        self.db.refresh(obj)
        return obj
