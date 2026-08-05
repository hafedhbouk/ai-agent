from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from app.core.logging import get_logger

ServiceType = TypeVar("ServiceType")
logger = get_logger("service")


class BaseService(ABC, Generic[ServiceType]):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[ServiceType]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ServiceType]:
        raise NotImplementedError

    @abstractmethod
    def create(self, obj_in: Dict[str, Any]) -> ServiceType:
        raise NotImplementedError

    @abstractmethod
    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ServiceType]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int) -> bool:
        raise NotImplementedError
