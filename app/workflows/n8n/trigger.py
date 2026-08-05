from typing import Dict, Any, Optional, List
from app.workflows.n8n.schemas import WorkflowDefinition, WorkflowExecution
from app.workflows.n8n.executor import executor
from app.core.logging import get_logger

logger = get_logger("workflows.n8n.trigger")


class WorkflowTrigger:
    def __init__(self):
        self._triggers: Dict[str, Dict[str, Any]] = {}

    def register_trigger(
        self,
        trigger_id: str,
        workflow_id: str,
        trigger_type: str,
        config: Dict[str, Any],
    ) -> None:
        self._triggers[trigger_id] = {
            "trigger_id": trigger_id,
            "workflow_id": workflow_id,
            "trigger_type": trigger_type,
            "config": config,
        }
        logger.info(f"Trigger registered: {trigger_id} -> {workflow_id}")

    def unregister_trigger(self, trigger_id: str) -> bool:
        if trigger_id in self._triggers:
            del self._triggers[trigger_id]
            logger.info(f"Trigger unregistered: {trigger_id}")
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        return self._triggers.get(trigger_id)

    def list_triggers(self) -> List[Dict[str, Any]]:
        return list(self._triggers.values())

    def get_triggers_for_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        return [
            t for t in self._triggers.values()
            if t["workflow_id"] == workflow_id
        ]

    async def fire_trigger(
        self,
        trigger_id: str,
        payload: Dict[str, Any],
    ) -> Optional[WorkflowExecution]:
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            logger.error(f"Trigger '{trigger_id}' not found")
            return None

        workflow_id = trigger["workflow_id"]
        from app.workflows.n8n.schemas import N8nWebhookPayload
        from datetime import datetime

        webhook_payload = N8nWebhookPayload(
            workflow_id=workflow_id,
            workflow_name=workflow_id,
            trigger_node=trigger_id,
            execution_id=f"trigger_{trigger_id}_{datetime.utcnow().isoformat()}",
            data=payload,
        )

        execution = await executor.execute(
            workflow_id=workflow_id,
            payload=webhook_payload,
        )
        return execution


trigger_manager = WorkflowTrigger()


def get_trigger_manager() -> WorkflowTrigger:
    return trigger_manager