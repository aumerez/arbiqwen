"""Tests for Plane agent tools: client request shape, tool callables, registry,
and a loop round that calls a tool end-to-end."""

import json

import pytest

from app.agents import loop as loop_mod
from app.agents import runner as runner_mod
from app.agents.loop import run_agent
from app.agents.models import AgentDefinition, AgentRun, AgentStatus
from app.agents.tools import build_registry
from app.integrations import plane_client

# --- fake httpx -----------------------------------------------------------


class FakeResp:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data
        self.text = json.dumps(data)

    def json(self):
        return self._data


class FakeClient:
    calls: dict = {}

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json, headers):
        FakeClient.calls["post"] = {"url": url, "json": json, "headers": headers}
        return FakeResp(
            201, {"id": "uuid-1", "sequence_id": 42, "name": json["name"], "priority": json.get("priority")}
        )

    async def get(self, url, headers):
        FakeClient.calls["get"] = {"url": url, "headers": headers}
        return FakeResp(200, {"results": [{"id": "a", "sequence_id": 1, "name": "existing"}]})


@pytest.fixture
def plane_env(monkeypatch):
    monkeypatch.setattr(plane_client.settings, "PLANE_BASE_URL", "https://plane.test", raising=False)
    monkeypatch.setattr(plane_client.settings, "PLANE_API_KEY", "key-123", raising=False)
    monkeypatch.setattr(plane_client.settings, "PLANE_WORKSPACE_SLUG", "acme", raising=False)
    monkeypatch.setattr(plane_client.settings, "PLANE_PROJECT_ID", "proj-9", raising=False)
    monkeypatch.setattr(plane_client.httpx, "AsyncClient", FakeClient)
    FakeClient.calls = {}


# --- client ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_task_builds_request(plane_env):
    out = await plane_client.create_task(name="Fix pump", priority="high")
    call = FakeClient.calls["post"]
    assert call["url"] == "https://plane.test/api/v1/workspaces/acme/projects/proj-9/issues/"
    assert call["headers"]["X-API-Key"] == "key-123"
    assert call["json"] == {"name": "Fix pump", "priority": "high"}
    assert out["sequence_id"] == 42


@pytest.mark.asyncio
async def test_create_task_coerces_bad_priority(plane_env):
    await plane_client.create_task(name="x", priority="ASAP")
    assert FakeClient.calls["post"]["json"]["priority"] == "none"


@pytest.mark.asyncio
async def test_create_task_uses_explicit_project(plane_env):
    await plane_client.create_task(name="x", project_id="other-proj")
    assert "projects/other-proj/issues/" in FakeClient.calls["post"]["url"]


@pytest.mark.asyncio
async def test_client_raises_when_not_configured(monkeypatch):
    monkeypatch.setattr(plane_client.settings, "PLANE_BASE_URL", None, raising=False)
    with pytest.raises(plane_client.PlaneNotConfigured):
        await plane_client.create_task(name="x")


# --- tools + registry -----------------------------------------------------


def test_build_registry_filters_by_allowed():
    registry, defs = build_registry(["plane_create_task", "not_a_tool"])
    assert set(registry) == {"plane_create_task"}
    assert [d["name"] for d in defs] == ["plane_create_task"]


def test_build_registry_empty():
    assert build_registry([]) == ({}, [])


@pytest.mark.asyncio
async def test_plane_create_task_tool_success(plane_env):
    registry, _ = build_registry(["plane_create_task"])
    result = await registry["plane_create_task"]({"name": "Follow up with Acme", "priority": "high"})
    assert result["sequence_id"] == 42
    assert "error" not in result


@pytest.mark.asyncio
async def test_plane_create_task_tool_missing_name(plane_env):
    registry, _ = build_registry(["plane_create_task"])
    result = await registry["plane_create_task"]({})
    assert result["error"] == "name is required"


@pytest.mark.asyncio
async def test_plane_tool_reports_not_configured(monkeypatch):
    monkeypatch.setattr(plane_client.settings, "PLANE_BASE_URL", None, raising=False)
    registry, _ = build_registry(["plane_create_task"])
    result = await registry["plane_create_task"]({"name": "x"})
    assert "not configured" in result["error"].lower()


# --- loop integration -----------------------------------------------------


class FakeProvider:
    provider_key = "fake"
    model = "fake-model"

    def __init__(self, rounds):
        # rounds: list of event-lists, one per generate_stream call
        self._rounds = list(rounds)

    async def generate_stream(self, messages, tools=None):
        events = self._rounds.pop(0)
        for e in events:
            yield e


@pytest.mark.asyncio
async def test_loop_calls_plane_tool_end_to_end(monkeypatch, session_factory, db, plane_env):
    monkeypatch.setattr(loop_mod, "AsyncSessionLocal", session_factory)
    # Round 1: model calls the tool. Round 2: model writes the final answer.
    provider = FakeProvider(
        [
            [{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {"name": "Call Acme"}}],
            [{"type": "text", "text": "Created task OPS-42 for Acme."}, {"type": "end_turn"}],
        ]
    )
    monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: provider)

    definition = AgentDefinition(
        name="Lead Intake",
        prompt_template="Create a follow-up task",
        allowed_tools=["plane_create_task"],
        user_id=1,
        tenant_id=1,
    )
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    run = AgentRun(definition_id=definition.id, user_id=1, tenant_id=1, status=AgentStatus.draft.value)
    db.add(run)
    await db.commit()
    await db.refresh(run)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.done.value
    assert "OPS-42" in run.result_md
    # The tool actually hit the (faked) Plane client.
    assert FakeClient.calls["post"]["json"]["name"] == "Call Acme"


@pytest.mark.asyncio
async def test_loop_blocks_tool_outside_allowlist(monkeypatch, session_factory, db):
    monkeypatch.setattr(loop_mod, "AsyncSessionLocal", session_factory)
    provider = FakeProvider([[{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {"name": "x"}}]])
    monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: provider)

    # allowed_tools is empty → the tool is not exposed and calling it is blocked.
    definition = AgentDefinition(name="No Tools", prompt_template="do it", allowed_tools=[], user_id=1, tenant_id=1)
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    run = AgentRun(definition_id=definition.id, user_id=1, tenant_id=1, status=AgentStatus.draft.value)
    db.add(run)
    await db.commit()
    await db.refresh(run)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.failed.value
    assert run.error["reason"] == "tool_not_allowed"
