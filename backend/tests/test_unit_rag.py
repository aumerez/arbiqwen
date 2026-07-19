"""Unit tests for the guarded RAG helpers and embeddings factory."""

from app.chat.retrieval import retrieve
from app.embeddings import EmbeddingProvider, get_embedding_provider


async def test_retrieve_without_key_returns_empty(monkeypatch):
    from app.chat import retrieval

    monkeypatch.setattr(retrieval.settings, "DASHSCOPE_API_KEY", None, raising=False)
    monkeypatch.setattr(retrieval.settings, "OPENAI_API_KEY", None, raising=False)
    assert await retrieve("anything") == []


def test_embedding_provider_default_dimension():
    p = get_embedding_provider()
    assert isinstance(p, EmbeddingProvider)
    assert p.dimension == 1024  # text-embedding-v3 (DashScope) default
