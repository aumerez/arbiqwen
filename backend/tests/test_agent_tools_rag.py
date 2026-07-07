"""Tests for the rag_search agent tool (read-only knowledge grounding)."""

import pytest

from app.agents import tools as tools_mod
from app.agents.tools import build_registry
from app.chat.retrieval import RetrievedChunk


@pytest.fixture
def fake_retrieve(monkeypatch):
    """Stub retrieval so the tool test needs no embeddings/Qdrant."""
    calls: list[tuple] = []

    async def fake(query, top_k=5):
        calls.append((query, top_k))
        return [
            RetrievedChunk(text="Acme signed in 2024.", score=0.91, document_id=3, chunk_index=0),
            RetrievedChunk(text="Acme prefers email.", score=0.82, document_id=3, chunk_index=1),
        ]

    monkeypatch.setattr(tools_mod, "retrieve", fake)
    return calls


def test_registry_includes_rag_search():
    registry, defs = build_registry(["rag_search"])
    assert "rag_search" in registry
    assert defs[0]["name"] == "rag_search"


@pytest.mark.asyncio
async def test_rag_search_returns_results(fake_retrieve):
    registry, _ = build_registry(["rag_search"])
    out = await registry["rag_search"]({"query": "what do we know about Acme?"})
    assert out["count"] == 2
    assert out["results"][0]["document_id"] == 3
    assert "Acme" in out["results"][0]["text"]
    assert fake_retrieve[0][0] == "what do we know about Acme?"


@pytest.mark.asyncio
async def test_rag_search_clamps_top_k(fake_retrieve):
    registry, _ = build_registry(["rag_search"])
    await registry["rag_search"]({"query": "x", "top_k": 999})
    assert fake_retrieve[0][1] == 20  # clamped to max


@pytest.mark.asyncio
async def test_rag_search_requires_query(fake_retrieve):
    registry, _ = build_registry(["rag_search"])
    out = await registry["rag_search"]({})
    assert out["error"] == "query is required"


@pytest.mark.asyncio
async def test_rag_search_empty_when_unconfigured(monkeypatch):
    async def empty(query, top_k=5):
        return []

    monkeypatch.setattr(tools_mod, "retrieve", empty)
    registry, _ = build_registry(["rag_search"])
    out = await registry["rag_search"]({"query": "anything"})
    assert out == {"count": 0, "results": []}
