from typing import Dict, Any, Optional, List
from datetime import datetime, uuid
from app.workflows.n8n.schemas import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    N8nWebhookPayload,
)
from app.agents.manager import AgentManager
from app.core.logging import get_logger

logger = get_logger("workflows.n8n.executor")


class WorkflowExecutor:
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._agent_manager = AgentManager()

    def register_workflow(self, definition: Dict[str, Any]) -> WorkflowDefinition:
        workflow = WorkflowDefinition(**definition)
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"Workflow registered: {workflow.name}")
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        return [
            {
                "workflow_id": w.workflow_id,
                "name": w.name,
                "description": w.description,
                "active": w.active,
                "step_count": len(w.steps),
            }
            for w in self._workflows.values()
        ]

    async def execute(
        self,
        workflow_id: str,
        payload: N8nWebhookPayload,
        db: Any = None,
    ) -> WorkflowExecution:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running",
        )
        self._executions[execution_id] = execution

        try:
            results = {}
            for step in workflow.steps:
                execution.current_step = step.step_id
                step_result = await self._execute_step(step, payload, db)
                results[step.step_id] = step_result

                if step.next_step is None and step_result.get("status") == "error":
                    execution.status = "failed"
                    execution.error = step_result.get("error")
                    break
            else:
                execution.status = "completed"
                execution.results = results

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            logger.error(f"Workflow execution failed: {e}")

        execution.completed_at = datetime.utcnow()
        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
        db: Any = None,
    ) -> Dict[str, Any]:
        if step.step_type == "agent":
            return await self._execute_agent_step(step, payload, db)
        elif step.step_type == "tool":
            return await self._execute_tool_step(step, payload, db)
        elif step.step_type == "condition":
            return self._execute_condition_step(step, payload)
        elif step.step_type == "http_request":
            return self._execute_http_step(step, payload)
        elif step.step_type == "transform":
            return self._execute_transform_step(step, payload)
        else:
            return {"status": "error", "error": f"Unknown step type: {step.step_type}"}

    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
        db: Any = None,
    ) -> Dict[str, Any]:
        agent_name = step.agent_name
        if not agent_name:
            return {"status": "error", "error": "No agent_name specified"}

        try:
            self._agent_manager.load_agents()
            agent = self._agent_manager.get_agent(agent_name)
            message = payload.data.get("message", "")
            from app.agents.base import AgentContext
            context = AgentContext(
                metadata={"workflow_id": payload.workflow_id, "step_id": step.step_id},
            )
            response = await agent.run(message, context)
            return {"status": "success", "result": response.content}
        except Exception as e:
            logger.error(f"Agent step '{step.step_id}' failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_tool_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
        db: Any = None,
    ) -> Dict[str, Any]:
        tool_name = step.tool_name
        if not tool_name:
            return {"status": "error", "error": "No tool_name specified"}

        try:
            from app.tools.manager import ToolManager
            tm = ToolManager()
            tool = tm.get_tool(tool_name)
            if tool is None:
                return {"status": "error", "error": f"Tool '{tool_name}' not found"}

            result = tool.execute(**step.parameters)
            return {"status": "success", "result": result.model_dump() if hasattr(result, "model_dump") else str(result)}
        except Exception as e:
            logger.error(f"Tool step '{step.step_id}' failed: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_condition_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
    ) -> Dict[str, Any]:
        condition = step.condition or ""
        try:
            result = eval(condition, {"__builtins__": {}}, payload.data)
            return {"status": "success", "result": bool(result)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _execute_http_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
    ) -> Dict[str, Any]:
        import requests
        url = step.parameters.get("url")
        method = step.parameters.get("method", "GET").upper()
        headers = step.parameters.get("headers", {})
        data = step.parameters.get("data")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return {"status": "error", "error": f"Unsupported HTTP method: {method}"}

            return {
                "status": "success",
                "result": {
                    "status_code": response.status_code,
                    "body": response.text[:2000],
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _execute_transform_step(
        self,
        step: WorkflowStep,
        payload: N8nWebhookPayload,
    ) -> Dict[str, Any]:
        transform = step.parameters.get("transform", {})
        source_key = transform.get("source_key", "")
        target_key = transform.get("target_key", "")
        operation = transform.get("operation", "copy")

        try:
            source_value = payload.data.get(source_key, "")
            if operation == "copy":
                return {"status": "success", "result": {target_key: source_value}}
            elif operation == "uppercase":
                return {"status": "success", "result": {target_key: str(source_value).upper()}}
            elif operation == "lowercase":
                return {"status": "success", "result": {target_key: str(source_value).lower()}}
            elif operation == "append":
                suffix = transform.get("suffix", "")
                return {"status": "success", "result": {target_key: str(source_value) + suffix}}
            else:
                return {"status": "error", "error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self._executions.get(execution_id)


executor = WorkflowExecutor()


def get_workflow_executor() -> WorkflowExecutor:
    return executor