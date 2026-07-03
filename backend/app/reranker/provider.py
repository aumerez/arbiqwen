"""Reranker for improving retrieval quality in the RAG pipeline.

Provides an abstract reranker interface and two implementations:
- LocalReranker — a sentence-transformers cross-encoder, loaded once and reused
- PassThroughReranker — a no-op used when reranking is disabled
"""

import asyncio
import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class Reranker(ABC):
    """Abstract reranker interface for scoring query-chunk relevance."""

    @abstractmethod
    async def rerank(self, query: str, chunks: list[str], top_k: int = 5) -> list[str]:
        """Rerank text chunks by relevance to the query, keeping the top_k."""

    @abstractmethod
    async def score(self, query: str, texts: list[str]) -> list[float]:
        """Compute relevance scores for texts against the query."""


class LocalReranker(Reranker):
    """Local cross-encoder reranker using sentence-transformers.

    The CrossEncoder model is loaded once on first instantiation and reused —
    loading the weight files on every chat message would be prohibitively slow.
    """

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import CrossEncoder

        self.model_name = model_name or settings.RERANKER_MODEL
        logger.info("Loading reranker model: %s", self.model_name)
        self.model = CrossEncoder(self.model_name)
        logger.info("Reranker model loaded")

    async def rerank(self, query: str, chunks: list[str], top_k: int = 5) -> list[str]:
        pairs = [(query, chunk) for chunk in chunks]
        scores = await asyncio.to_thread(self.model.predict, pairs)
        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in ranked[:top_k]]

    async def score(self, query: str, texts: list[str]) -> list[float]:
        pairs = [(query, text) for text in texts]
        return await asyncio.to_thread(self.model.predict, pairs)


class PassThroughReranker(Reranker):
    """No-op reranker used when ENABLE_RERANKER is false."""

    async def rerank(self, query: str, chunks: list[str], top_k: int = 5) -> list[str]:
        return chunks[:top_k]

    async def score(self, query: str, texts: list[str]) -> list[float]:
        return [1.0] * len(texts)


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Return the cached reranker (singleton).

    The cross-encoder model is loaded on first call and reused across requests.
    """
    global _reranker
    if _reranker is None:
        if not settings.ENABLE_RERANKER:
            _reranker = PassThroughReranker()
        else:
            _reranker = LocalReranker()
    return _reranker
