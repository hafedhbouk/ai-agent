from typing import Optional, Dict, Any, List
import time
from app.agents.base import BaseAgent, AgentResponse, AgentContext
from app.agents.schemas import AgentYAMLConfig
from app.core.logging import get_logger

logger = get_logger("agents.generic")


class GenericAgent(BaseAgent):
    async def run(self, message: str, context: Optional[AgentContext] = None) -> AgentResponse:
        start = time.time()
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            llm = ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{message}"),
            ])

            chain = prompt | llm
            history = []
            if context and context.metadata.get("history"):
                history = context.metadata["history"]

            response = await chain.ainvoke({"message": message, "history": history})
            content = response.content if hasattr(response, "content") else str(response)
            latency = int((time.time() - start) * 1000)
            tokens = getattr(response, "usage_metadata", {}).get("total_tokens") if hasattr(response, "usage_metadata") else None

            return AgentResponse(
                content=content,
                tokens_used=tokens,
                latency_ms=latency,
                model=self.model_name,
            )
        except Exception as e:
            logger.error(f"GenericAgent '{self.name}' failed: {e}")
            raise

    async def stream(self, message: str, context: Optional[AgentContext] = None):
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            llm = ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens, streaming=True)
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{message}"),
            ])
            chain = prompt | llm
            history = []
            if context and context.metadata.get("history"):
                history = context.metadata["history"]

            async for chunk in chain.astream({"message": message, "history": history}):
                yield chunk
        except Exception as e:
            logger.error(f"GenericAgent '{self.name}' streaming failed: {e}")
            raise
