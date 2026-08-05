from typing import Optional, Dict, Any, List
import time
from app.agents.base import BaseAgent, AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.agents.langgraph.graph_builder import build_single_agent_graph
from app.agents.langgraph.orchestrator import orchestrator
from app.core.logging import get_logger

logger = get_logger("agents.generic")


class GenericAgent(BaseAgent):
    def __init__(self, config: AgentYAMLConfig, tools: Optional[List[Any]] = None, **kwargs):
        super().__init__(config, **kwargs)
        self.tools = tools or []
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            self._graph = build_single_agent_graph(
                agent_name=self.name,
                llm=llm,
                tools=self.tools if self.tools else None,
                system_prompt=self.system_prompt,
                max_iterations=5,
            )
        return self._graph

    async def run(self, message: str, context: Optional[AgentContext] = None) -> AgentResponse:
        start = time.time()
        try:
            if self.name in orchestrator.list_agents():
                result = orchestrator.run_single_agent(
                    agent_name=self.name,
                    user_message=message,
                    config={"max_iterations": 5},
                )
                latency = int((time.time() - start) * 1000)
                return AgentResponse(
                    content=result.get("result", ""),
                    tokens_used=None,
                    latency_ms=latency,
                    model=self.model_name,
                    sources=result.get("sources", []),
                )
            return await self._direct_run(message, context, start)
        except Exception as e:
            logger.error(f"GenericAgent '{self.name}' failed: {e}")
            raise

    async def _direct_run(self, message: str, context: Optional[AgentContext], start: float) -> AgentResponse:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        llm = ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)
        history = []
        rag_context = ""
        if context:
            history = context.metadata.get("history", []) or []
            rag_context = self._format_rag_context(context.metadata.get("rag_context"))
        system_prompt = self.system_prompt
        if rag_context:
            system_prompt = f"{self.system_prompt}\n\n## Contexte RAG\n{rag_context}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{message}"),
        ])
        chain = prompt | llm
        response = await chain.ainvoke({"message": message, "history": history})
        content = response.content if hasattr(response, "content") else str(response)
        latency = int((time.time() - start) * 1000)
        usage = getattr(response, "usage_metadata", None)
        tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
        return AgentResponse(
            content=content,
            tokens_used=tokens,
            latency_ms=latency,
            model=self.model_name,
        )

    @staticmethod
    def _format_rag_context(rag_results: Optional[List[Dict[str, Any]]]) -> str:
        if not rag_results:
            return ""
        lines = []
        for idx, item in enumerate(rag_results, 1):
            text = item.get("text") or item.get("content") or item.get("document") or ""
            source = item.get("source") or item.get("metadata", {}).get("source") or ""
            lines.append(f"{idx}. {text}")
            if source:
                lines.append(f"   Source: {source}")
        return "\n".join(lines)

    async def stream(self, message: str, context: Optional[AgentContext] = None):
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                streaming=True,
            )
            history = []
            rag_context = ""
            if context:
                history = context.metadata.get("history", []) or []
                rag_context = self._format_rag_context(context.metadata.get("rag_context"))
            system_prompt = self.system_prompt
            if rag_context:
                system_prompt = f"{self.system_prompt}\n\n## Contexte RAG\n{rag_context}"
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{message}"),
            ])
            chain = prompt | llm
            async for chunk in chain.astream({"message": message, "history": history}):
                yield chunk
        except Exception as e:
            logger.error(f"GenericAgent '{self.name}' streaming failed: {e}")
            raise
