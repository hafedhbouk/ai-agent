from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.workflows.n8n.schemas import (
    N8nWebhookPayload,
    WorkflowExecution,
    WebhookResponse,
)
from app.workflows.n8n.executor import WorkflowExecutor
from app.database.session import get_db
from app.core.logging import get_logger

logger = get_logger("workflows.n8n.webhook")
router = APIRouter()

_executor = WorkflowExecutor()


@router.post("/webhook/{workflow_id}", summary="Receive n8n webhook payload")
async def n8n_webhook(
    workflow_id: str,
    payload: N8nWebhookPayload,
    db: Session = Depends(get_db),
):
    try:
        execution = await _executor.execute(
            workflow_id=workflow_id,
            payload=payload,
            db=db,
        )
        return WebhookResponse(
            execution_id=execution.execution_id,
            status=execution.status,
            message="Workflow executed successfully",
            result=execution.results,
        )
    except Exception as e:
        logger.error(f"Webhook execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/{workflow_id}/status/{execution_id}", summary="Get execution status")
def get_execution_status(
    workflow_id: str,
    execution_id: str,
    db: Session = Depends(get_db),
):
    execution = _executor.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/workflows", summary="List all workflows")
def list_workflows():
    return _executor.list_workflows()


@router.post("/workflows", summary="Register a new workflow")
def register_workflow(definition: Dict[str, Any]):
    return _executor.register_workflow(definition)


@router.post("/trigger/{workflow_id}", summary="Trigger a workflow manually")
async def trigger_workflow(
    workflow_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    try:
        execution = await _executor.execute(
            workflow_id=workflow_id,
            payload=N8nWebhookPayload(
                workflow_id=workflow_id,
                workflow_name=workflow_id,
                trigger_node="manual",
                execution_id=f"manual_{workflow_id}",
                data=payload,
            ),
            db=db,
        )
        return WebhookResponse(
            execution_id=execution.execution_id,
            status=execution.status,
            message="Workflow triggered successfully",
            result=execution.results,
        )
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))