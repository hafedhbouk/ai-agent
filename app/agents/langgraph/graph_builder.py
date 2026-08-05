from typing import Callable, Dict, Any, Optional, List
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from app.agents.langgraph.state import AgentState, MultiAgentState, Messages
from app.core.logging import get_logger

logger = get_logger("agents.langgraph.graph_builder")

logger = get_logger("agents.langgraph.graph_builder")


def build_single_agent_graph(
    agent_name: str,
    llm: Any,
    tools: Optional[List[Any]] = None,
    system_prompt: str = "",
    max_iterations: int = 5,
) -> StateGraph:
    workflow = StateGraph(AgentState)

    def agent_node(state: AgentState) -> dict:
        messages = state.get("messages", [])
        if system_prompt:
            messages = [SystemMessage(content=system_prompt)] + messages
        user_msg = HumanMessage(content=state.get("user_message", ""))
        messages.append(user_msg)

        if tools:
            llm_with_tools = llm.bind_tools(tools)
            response = llm_with_tools.invoke(messages)
        else:
            response = llm.invoke(messages)

        new_messages = list(messages) + [response]
        return {
            "messages": new_messages,
            "result": response.content if hasattr(response, "content") else str(response),
            "iteration": state.get("iteration", 0) + 1,
        }

    def should_continue(state: AgentState) -> str:
        iteration = state.get("iteration", 0)
        max_it = state.get("max_iterations", 5)
        result = state.get("result")
        if result and iteration >= 1:
            return END
        if iteration >= max_it:
            return END
        return "agent"

    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"agent": "agent", END: END})

    return workflow


def build_multi_agent_graph(
    agent_definitions: Dict[str, dict],
    llm: Any,
    orchestrator_prompt: str = "",
    max_iterations: int = 10,
) -> StateGraph:
    workflow = StateGraph(MultiAgentState)

    def orchestrator_node(state: MultiAgentState) -> dict:
        messages = state.get("messages", [])
        if orchestrator_prompt:
            messages = [SystemMessage(content=orchestrator_prompt)] + messages
        user_msg = HumanMessage(content=state.get("user_message", ""))
        messages.append(user_msg)

        active = state.get("active_agent", "")
        queue = state.get("agent_queue", [])
        context = state.get("context", {})

        context_str = f"\nAgent actif: {active}\nFile d'attente: {queue}\nContexte: {context}"
        messages.append(HumanMessage(content=f"Orchestration:\n{context_str}"))

        response = llm.invoke(messages)
        return {
            "messages": messages + [response],
            "iteration": state.get("iteration", 0) + 1,
            "results": {**state.get("results", {}), active: response.content if hasattr(response, "content") else str(response)},
        }

    def agent_node_factory(agent_name: str, agent_config: dict) -> Callable:
        def node(state: MultiAgentState) -> dict:
            messages = state.get("messages", [])
            system_msg = agent_config.get("system_prompt", "")
            if system_msg:
                messages = [SystemMessage(content=system_msg)] + messages
            user_msg = HumanMessage(content=state.get("user_message", ""))
            messages.append(user_msg)

            tools = agent_config.get("tools", [])
            if tools:
                llm_with_tools = llm.bind_tools(tools)
                response = llm_with_tools.invoke(messages)
            else:
                response = llm.invoke(messages)

            return {
                "messages": messages + [response],
                "results": {**state.get("results", {}), agent_name: response.content if hasattr(response, "content") else str(response)},
                "completed_agents": state.get("completed_agents", []) + [agent_name],
            }
        return node

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.set_entry_point("orchestrator")

    for agent_name, agent_config in agent_definitions.items():
        workflow.add_node(agent_name, agent_node_factory(agent_name, agent_config))
        workflow.add_edge("orchestrator", agent_name)

    def should_continue_multi(state: MultiAgentState) -> str:
        iteration = state.get("iteration", 0)
        max_it = state.get("max_iterations", 10)
        completed = state.get("completed_agents", [])
        queue = state.get("agent_queue", [])
        if iteration >= max_it or not queue or len(completed) >= len(agent_definitions):
            return END
        return queue[0] if queue else END

    for agent_name in agent_definitions:
        workflow.add_conditional_edges(agent_name, should_continue_multi, {END: END})

    return workflow