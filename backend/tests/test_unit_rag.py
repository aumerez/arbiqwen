"""Unit tests for the guarded RAG helpers and embeddings factory."""

import pytest

from app.chat.retrieval import RetrievedChunk, retrieve
from app.chat.service import SYSTEM_PROMPT, _build_prompt
from app.embeddings import EmbeddingProvider, get_embedding_provider


async def test_retrieve_without_key_returns_empty(monkeypatch):
    from app.chat import retrieval

    monkeypatch.setattr(retrieval.settings, "OPENAI_API_KEY", None, raising=False)
    assert await retrieve("anything") == []


def test_build_prompt_without_context():
    prompt = _build_prompt("What is Arbi?", [])
    assert SYSTEM_PROMPT in prompt
    assert "What is Arbi?" in prompt
    assert "Context:" not in prompt


def test_build_prompt_with_context():
    chunks = [RetrievedChunk(text="Arbi is an assistant.", score=0.9, document_id=1, chunk_index=0)]
    prompt = _build_prompt("What is Arbi?", chunks)
    assert "Context:" in prompt
    assert "Arbi is an assistant." in prompt


def test_embedding_provider_default_dimension():
    p = get_embedding_provider()
    assert isinstance(p, EmbeddingProvider)
    assert p.dimension == 1536  # matches the default Qdrant collection
