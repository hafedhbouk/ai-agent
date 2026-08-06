from typing import Any
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("llm.providers")


class LLMProviderFactory:
    @staticmethod
    def create() -> BaseChatModel:
        provider = settings.llm_provider.lower()
        logger.info(f"Creating LLM provider: {provider}")
        if provider == "ollama":
            return LLMProviderFactory._create_ollama()
        if provider == "groq":
            return LLMProviderFactory._create_groq()
        if provider == "openai":
            return LLMProviderFactory._create_openai()
        raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _create_openai() -> BaseChatModel:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        return ChatOpenAI(
            model=settings.llm_model or settings.openai_model,
            temperature=0.7,
            max_tokens=4096,
        )

    @staticmethod
    def _create_groq() -> BaseChatModel:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when using Groq provider")
        return ChatGroq(
            model=settings.groq_model,
            temperature=0.7,
            max_tokens=4096,
        )

    @staticmethod
    def _create_ollama() -> BaseChatModel:
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.7,
        )
