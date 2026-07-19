"""Tests for app.agents.memory — save_memory and recall_memories."""

from __future__ import annotations

import pytest

from app.agents import memory as mem_mod
from app.agents.memory import recall_memories, save_memory
from app.agents.models import AgentMemory, AgentStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeRun:
    def __init__(
        self,
        *,
        run_id=1,
        tenant_id=1,
        definition_id=1,
        trigger_input="Acme pricing inquiry",
        result_md="Created task #5.",
    ):
        self.id = run_id
        self.tenant_id = tenant_id
        self.definition_id = definition_id
        self.trigger_input = trigger_input
        self.result_md = result_md
        self.status = AgentStatus.done.value


def _make_run(**kw) -> _FakeRun:
    return _FakeRun(**kw)


class _FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


# ---------------------------------------------------------------------------
# save_memory — unconfigured (no OPENAI_API_KEY)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_memory_skips_when_unconfigured(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(mem_mod.settings, "DASHSCOPE_API_KEY", "")
    session = _FakeSession()
    result = await save_memory(session, run=_make_run())
    assert result is None
    assert session.added == []


# ---------------------------------------------------------------------------
# save_memory — configured path (Qdrant stubbed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_memory_stores_row_when_qdrant_fails(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr(mem_mod, "_is_configured", lambda: True)

    session = _FakeSession()
    run = _make_run()

    async def fake_embed_text(text):
        return [0.0] * 4

    monkeypatch.setattr(
        "app.embeddings.get_embedding_provider", lambda: type("E", (), {"embed_text": staticmethod(fake_embed_text)})()
    )

    async def bad_upsert2(*a, **kw):
        raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr("app.qdrant.get_qdrant_client", lambda: type("Q", (), {"upsert": staticmethod(bad_upsert2)})())
    monkeypatch.setattr("app.qdrant.ensure_collection", lambda name: None)

    result = await save_memory(session, run=run)
    assert result is not None
    assert isinstance(result, AgentMemory)
    assert result.summary.startswith("Input:")
    assert result.qdrant_id is None  # Qdrant failed → no id
    assert session.committed


@pytest.mark.asyncio
async def test_save_memory_stores_row_with_qdrant_id(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr(mem_mod, "_is_configured", lambda: True)

    upserted = {}

    async def fake_embed_text(text):
        return [0.1] * 4

    async def fake_upsert(collection_name, points):
        upserted["id"] = points[0].id

    monkeypatch.setattr(
        "app.embeddings.get_embedding_provider", lambda: type("E", (), {"embed_text": staticmethod(fake_embed_text)})()
    )
    monkeypatch.setattr("app.qdrant.get_qdrant_client", lambda: type("Q", (), {"upsert": staticmethod(fake_upsert)})())

    async def noop(name):
        pass

    monkeypatch.setattr("app.qdrant.ensure_collection", noop)

    session = _FakeSession()
    run = _make_run()
    result = await save_memory(session, run=run)

    assert result is not None
    assert result.qdrant_id == upserted["id"]
    assert result.run_id == run.id
    assert result.tenant_id == run.tenant_id


# ---------------------------------------------------------------------------
# recall_memories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recall_memories_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(mem_mod.settings, "DASHSCOPE_API_KEY", "")
    result = await recall_memories(query="test", tenant_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_recall_memories_returns_none_on_empty_query(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    result = await recall_memories(query="  ", tenant_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_recall_memories_returns_none_when_no_hits(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr(mem_mod, "_is_configured", lambda: True)

    async def fake_embed(text):
        return [0.0] * 4

    class EmptyResult:
        points = []

    async def fake_query(*a, **kw):
        return EmptyResult()

    monkeypatch.setattr(
        "app.embeddings.get_embedding_provider", lambda: type("E", (), {"embed_text": staticmethod(fake_embed)})()
    )
    monkeypatch.setattr(
        "app.qdrant.get_qdrant_client", lambda: type("Q", (), {"query_points": staticmethod(fake_query)})()
    )

    result = await recall_memories(query="pricing", tenant_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_recall_memories_formats_hits(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr(mem_mod, "_is_configured", lambda: True)

    async def fake_embed(text):
        return [0.1] * 4

    class FakePoint:
        def __init__(self, summary):
            self.payload = {"summary": summary}

    class FakeResult:
        points = [FakePoint("Input: Acme pricing\nOutcome: Task #5 created.")]

    async def fake_query(*a, **kw):
        return FakeResult()

    monkeypatch.setattr(
        "app.embeddings.get_embedding_provider", lambda: type("E", (), {"embed_text": staticmethod(fake_embed)})()
    )
    monkeypatch.setattr(
        "app.qdrant.get_qdrant_client", lambda: type("Q", (), {"query_points": staticmethod(fake_query)})()
    )

    result = await recall_memories(query="pricing", tenant_id=1)
    assert result is not None
    assert "Relevant past runs" in result
    assert "Acme pricing" in result


@pytest.mark.asyncio
async def test_recall_memories_returns_none_on_qdrant_error(monkeypatch):
    monkeypatch.setattr(mem_mod.settings, "OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr(mem_mod, "_is_configured", lambda: True)

    async def fake_embed(text):
        return [0.0] * 4

    async def boom(*a, **kw):
        raise RuntimeError("unreachable")

    monkeypatch.setattr(
        "app.embeddings.get_embedding_provider", lambda: type("E", (), {"embed_text": staticmethod(fake_embed)})()
    )
    monkeypatch.setattr("app.qdrant.get_qdrant_client", lambda: type("Q", (), {"query_points": staticmethod(boom)})())

    result = await recall_memories(query="anything", tenant_id=1)
    assert result is None
