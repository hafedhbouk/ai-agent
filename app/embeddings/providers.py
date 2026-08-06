from typing import List, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("embeddings.providers")


class EmbeddingProviderFactory:
    @staticmethod
    def create():
        provider = settings.llm_provider.lower()
        logger.info(f"Creating embedding provider: {provider}")
        if provider == "ollama":
            return EmbeddingProviderFactory._create_ollama()
        return EmbeddingProviderFactory._create_openai()

    @staticmethod
    def _create_openai():
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            return OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model,
            )
        except ImportError:
            raise ImportError("chromadb is required for OpenAI embeddings. Install chromadb or use Ollama provider.")

    @staticmethod
    def _create_ollama():
        try:
            from langchain_ollama import OllamaEmbeddings
            from chromadb.utils.embedding_functions import EmbeddingFunction

            ollama_embeddings = OllamaEmbeddings(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url,
            )

            class OllamaChromaEmbeddingFunction(EmbeddingFunction):
                def __call__(self, input: List[str]) -> List[List[float]]:
                    return ollama_embeddings.embed_documents(input)

            return OllamaChromaEmbeddingFunction()
        except ImportError as e:
            raise ImportError(f"langchain-ollama is required for Ollama embeddings. Install it with: pip install langchain-ollama. Error: {e}")
