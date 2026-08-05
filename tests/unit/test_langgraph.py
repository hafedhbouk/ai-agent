import pytest
from app.agents.langgraph.state import AgentState, MultiAgentState
from app.agents.langgraph.graph_builder import build_single_agent_graph, build_multi_agent_graph
from app.agents.langgraph.orchestrator import LangGraphOrchestrator, orchestrator
from app.agents.langgraph.workflows import WORKFLOW_REGISTRY, list_workflows


def test_state_has_required_keys():
    state: AgentState = {
        "messages": [],
        "current_agent": "test",
        "user_message": "hello",
        "iteration": 0,
        "max_iterations": 5,
        "should_continue": True,
        "context": {},
    }
    assert state["current_agent"] == "test"
    assert state["iteration"] == 0


def test_multi_agent_state_has_required_keys():
    state: MultiAgentState = {
        "messages": [],
        "active_agent": "orchestrator",
        "agent_queue": ["agent1", "agent2"],
        "user_message": "hello",
        "iteration": 0,
        "max_iterations": 10,
        "completed_agents": [],
        "results": {},
        "should_continue": True,
        "context": {},
    }
    assert state["active_agent"] == "orchestrator"
    assert len(state["agent_queue"]) == 2


def test_orchestrator_is_singleton():
    o1 = orchestrator
    o2 = orchestrator
    assert o1 is o2


def test_orchestrator_initially_empty():
    assert orchestrator.list_agents() == []
    assert orchestrator.list_workflows() == []


def test_workflow_registry_not_empty():
    assert len(WORKFLOW_REGISTRY) >= 2
    assert "commerce_workflow" in WORKFLOW_REGISTRY
    assert "maintenance_workflow" in WORKFLOW_REGISTRY


def test_list_workflows():
    workflows = list_workflows()
    assert isinstance(workflows, list)
    assert len(workflows) >= 2


def test_single_agent_graph_has_nodes():
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    graph = build_single_agent_graph(
        agent_name="test_agent",
        llm=mock_llm,
        system_prompt="You are helpful.",
        max_iterations=3,
    )
    assert graph is not None
    nodes = [n for n in graph.nodes]
    assert "agent" in nodes


def test_multi_agent_graph_has_nodes():
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    agent_defs = {
        "agent1": {"system_prompt": "You are agent 1."},
        "agent2": {"system_prompt": "You are agent 2."},
    }
    graph = build_multi_agent_graph(
        agent_definitions=agent_defs,
        llm=mock_llm,
        orchestrator_prompt="Coordinate.",
        max_iterations=5,
    )
    assert graph is not None
    nodes = [n for n in graph.nodes]
    assert "orchestrator" in nodes
    assert "agent1" in nodes
    assert "agent2" in nodes