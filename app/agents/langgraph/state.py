from typing import TypedDict, List, Annotated, Any, Optional
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from app.core.logging import get_logger

logger = get_logger("agents.langgraph")


Messages = Annotated[List[BaseMessage], add]


class AgentState(TypedDict):
    messages: Messages
    current_agent: str
    target_agent: Optional[str]
    context: dict
    user_message: str
    iteration: int
    max_iterations: int
    should_continue: bool
    result: Optional[str]
    sources: List[dict]
    errors: List[str]


class MultiAgentState(TypedDict):
    messages: Messages
    active_agent: str
    agent_queue: List[str]
    context: dict
    user_message: str
    iteration: int
    max_iterations: int
    completed_agents: List[str]
    results: dict
    should_continue: bool
    final_result: Optional[str]
    errors: List[str]