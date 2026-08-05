from typing import Dict, Any, Optional, List
from app.agents.langgraph.state import AgentState, MultiAgentState
from app.agents.langgraph.graph_builder import build_single_agent_graph, build_multi_agent_graph
from app.core.logging import get_logger

logger = get_logger("agents.langgraph.orchestrator")


class LangGraphOrchestrator:
    def __init__(self):
        self.graphs: Dict[str, Any] = {}
        self.multi_agent_graphs: Dict[str, Any] = {}

    def register_single_agent(
        self,
        agent_name: str,
        llm: Any,
        tools: Optional[List[Any]] = None,
        system_prompt: str = "",
        max_iterations: int = 5,
    ) -> None:
        graph = build_single_agent_graph(agent_name, llm, tools, system_prompt, max_iterations)
        self.graphs[agent_name] = graph
        logger.info(f"Registered single-agent graph: {agent_name}")

    def register_multi_agent(
        self,
        workflow_name: str,
        agent_definitions: Dict[str, dict],
        llm: Any,
        orchestrator_prompt: str = "",
        max_iterations: int = 10,
    ) -> None:
        graph = build_multi_agent_graph(agent_definitions, llm, orchestrator_prompt, max_iterations)
        self.multi_agent_graphs[workflow_name] = graph
        logger.info(f"Registered multi-agent graph: {workflow_name}")

    def run_single_agent(
        self,
        agent_name: str,
        user_message: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if agent_name not in self.graphs:
            raise ValueError(f"Agent '{agent_name}' not registered")
        graph = self.graphs[agent_name]
        initial_state: AgentState = {
            "messages": [],
            "current_agent": agent_name,
            "user_message": user_message,
            "iteration": 0,
            "max_iterations": config.get("max_iterations", 5) if config else 5,
            "should_continue": True,
            "context": config or {},
        }
        thread_config = {"configurable": {"thread_id": agent_name}}
        result = graph.invoke(initial_state, config=thread_config)
        return {
            "agent_name": agent_name,
            "result": result.get("result"),
            "messages": result.get("messages", []),
            "iteration": result.get("iteration", 0),
        }

    def run_multi_agent(
        self,
        workflow_name: str,
        user_message: str,
        agent_queue: List[str],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if workflow_name not in self.multi_agent_graphs:
            raise ValueError(f"Workflow '{workflow_name}' not registered")
        graph = self.multi_agent_graphs[workflow_name]
        initial_state: MultiAgentState = {
            "messages": [],
            "active_agent": agent_queue[0] if agent_queue else "",
            "agent_queue": agent_queue,
            "user_message": user_message,
            "iteration": 0,
            "max_iterations": config.get("max_iterations", 10) if config else 10,
            "completed_agents": [],
            "results": {},
            "should_continue": True,
            "context": config or {},
        }
        thread_config = {"configurable": {"thread_id": workflow_name}}
        result = graph.invoke(initial_state, config=thread_config)
        return {
            "workflow_name": workflow_name,
            "final_result": result.get("result"),
            "results": result.get("results", {}),
            "completed_agents": result.get("completed_agents", []),
            "iteration": result.get("iteration", 0),
        }

    def get_graph(self, agent_name: str) -> Optional[Any]:
        return self.graphs.get(agent_name)

    def get_workflow(self, workflow_name: str) -> Optional[Any]:
        return self.multi_agent_graphs.get(workflow_name)

    def list_agents(self) -> List[str]:
        return list(self.graphs.keys())

    def list_workflows(self) -> List[str]:
        return list(self.multi_agent_graphs.keys())


orchestrator = LangGraphOrchestrator()


def get_orchestrator() -> LangGraphOrchestrator:
    return orchestrator