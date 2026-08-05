from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path


class AgentYAMLConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9_]+$")
    description: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    vector_collection: str = Field(..., min_length=1)
    database_tables: Optional[List[str]] = Field(default_factory=list)
    tools: Optional[List[str]] = Field(default_factory=list)
    model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1, le=128000)
    is_active: bool = Field(default=True)
    config_path: Optional[str] = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("Agent name must be alphanumeric with underscores only")
        return v.lower()

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("System prompt cannot be empty")
        return v.strip()

    @field_validator("vector_collection")
    @classmethod
    def validate_vector_collection(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Vector collection cannot be empty")
        return v.strip().lower().replace(" ", "_")
