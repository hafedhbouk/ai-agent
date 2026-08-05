from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger("workflows.n8n")


class N8nWebhookPayload(BaseModel):
    workflow_id: str
    workflow_name: str
    trigger_node: str
    execution_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorkflowStep(BaseModel):
    step_id: str
    step_type: str
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    condition: Optional[str] = None
    next_step: Optional[str] = None


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    trigger_type: str = "webhook"
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class WorkflowExecution(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class WebhookResponse(BaseModel):
    execution_id: str
    status: str
    message: str
    result: Optional[Any] = None