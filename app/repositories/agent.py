from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def get_by_id(self, id: int) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.id == id).first()

    def get_by_name(self, name: str) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Agent).filter(Agent.is_active == True).order_by(Agent.name).offset(skip).limit(limit).all()

    def get_active_agents(self) -> List[Agent]:
        return self.db.query(Agent).filter(Agent.is_active == True).all()

    def create(self, obj_in: dict) -> Agent:
        obj = Agent(**obj_in)
        self.db.add(obj)
        self._commit()
        self._refresh(obj)
        return obj

    def update(self, id: int, obj_in: dict) -> Optional[Agent]:
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
