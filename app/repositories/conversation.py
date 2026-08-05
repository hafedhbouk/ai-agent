from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, MessageRole
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def get_by_id(self, id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Conversation).order_by(Conversation.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100):
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_agent(self, agent_name: str, skip: int = 0, limit: int = 100):
        return (
            self.db.query(Conversation)
            .filter(Conversation.agent_name == agent_name)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj_in: dict) -> Conversation:
        obj = Conversation(**obj_in)
        self.db.add(obj)
        self._commit()
        self._refresh(obj)
        return obj

    def update(self, id: int, obj_in: dict) -> Optional[Conversation]:
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


class MessageRepository(BaseRepository[Message]):
    def get_by_id(self, id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Message).order_by(Message.created_at).offset(skip).limit(limit).all()

    def get_by_conversation(self, conversation_id: int) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

    def create(self, obj_in: dict) -> Message:
        obj = Message(**obj_in)
        self.db.add(obj)
        self._commit()
        self._refresh(obj)
        return obj

    def update(self, id: int, obj_in: dict) -> Optional[Message]:
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
