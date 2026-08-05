from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from app.models.base import BaseModel


class Agent(BaseModel):
    __tablename__ = "agents"

    name = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    vector_collection = Column(String(255), unique=True, index=True, nullable=False)
    database_tables = Column(JSON, nullable=True)
    tools = Column(JSON, nullable=True)
    model_name = Column(String(255), default="gpt-4o", nullable=False)
    temperature = Column(String(10), default="0.7", nullable=False)
    max_tokens = Column(Integer, default=4000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    config_path = Column(String(1024), nullable=True)
