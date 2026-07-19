"""Embedding provider interface and the OpenAI implementation.

Retrieval embeds text through `EmbeddingProvider`, mirroring the LLM provider
pattern: one abstract interface, a concrete implementation, and a settings-
driven factory. The client is built lazily so wiring works without credentials.
"""

import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    _cached_dimension: int | None = None

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""

    async def detect_dimension(self) -> int:
        """Probe the embedding dimension with a test call (cached)."""
        if self._cached_dimension is not None:
            return self._cached_dimension
        self._cached_dimension = len(await self.embed_text("dimension probe"))
        logger.info("Detected embedding dimension: %d", self._cached_dimension)
        return self._cached_dimension

    @property
    def dimension(self) -> int:
        """Cached dimension, or the configured default if not yet probed."""
        if self._cached_dimension is not None:
            return self._cached_dimension
        return settings.QDRANT_VECTOR_SIZE


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self._client = None

    @property
    def client(self):
        """Build the SDK client lazily so the provider constructs without a key."""
        if self._client is None:
            from openai import AsyncOpenAI

            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(input=[text], model=self.model, encoding_format="float")
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(input=texts, model=self.model, encoding_format="float")
        return [item.embedding for item in response.data]


class DashScopeEmbeddingProvider(OpenAIEmbeddingProvider):
    """DashScope embeddings — OpenAI-compatible endpoint, Alibaba API key.

    Uses text-embedding-v2 (1536-dim, same as OpenAI ada-002) so the Qdrant
    collection size is compatible with either provider.
    """

    def __init__(self):
        super().__init__(
            api_key=settings.DASHSCOPE_API_KEY,
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
            base_url=settings.DASHSCOPE_BASE_URL,
        )


_EMBEDDING_CLASSES: dict[str, type[EmbeddingProvider]] = {
    "openai": OpenAIEmbeddingProvider,
    "dashscope": DashScopeEmbeddingProvider,
}

_embedding_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the process-wide configured embedding provider (built once)."""
    global _embedding_provider
    if _embedding_provider is None:
        cls = _EMBEDDING_CLASSES.get(settings.EMBEDDING_PROVIDER)
        if cls is None:
            raise ValueError(f"Unknown embedding provider: {settings.EMBEDDING_PROVIDER}")
        _embedding_provider = cls()
    return _embedding_provider
