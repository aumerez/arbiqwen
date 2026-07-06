"""Tests for the single-loop runner (loop.run_agent) and the run trigger route."""

import pytest

from app.agents import loop as loop_mod
from app.agents import routes as routes_mod
from app.agents import runner as runner_mod
from app.agents.loop import run_agent
from app.agents.models import AgentStatus, AgentTask


class FakeProvider:
    provider_key = "fake"
    model = "fake-model"

    def __init__(self, events):
        self._events = events

    async def generate_stream(self, messages, tools=None):
        for event in self._events:
            yield event


@pytest.fixture
def wire_loop(monkeypatch, session_factory):
    """Point run_agent at the test DB and let callers set the provider stream."""
    monkeypatch.setattr(loop_mod, "AsyncSessionLocal", session_factory)

    def set_events(events):
        monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: FakeProvider(events))

    return set_events


async def _make_agent(db, prompt="summarize the pipeline", status=AgentStatus.draft):
    agent = AgentTask(
        title="Lead Intake",
        prompt_template=prompt,
        allowed_tools=[],
        user_id=1,
        tenant_id=1,
        status=status.value,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.mark.asyncio
async def test_run_agent_text_only_completes(wire_loop, db):
    wire_loop([{"type": "text", "text": "Pipeline looks healthy."}, {"type": "end_turn"}])
    agent = await _make_agent(db)

    await run_agent(agent.id)

    await db.refresh(agent)
    assert agent.status == AgentStatus.done.value
    assert agent.result_md == "Pipeline looks healthy."
    assert agent.started_at is not None
    assert agent.completed_at is not None


@pytest.mark.asyncio
async def test_run_agent_no_text_fails(wire_loop, db):
    # Model ends the turn with no text and no tools — nothing to deliver.
    wire_loop([{"type": "end_turn"}])
    agent = await _make_agent(db)

    await run_agent(agent.id)

    await db.refresh(agent)
    assert agent.status == AgentStatus.failed.value
    assert agent.error["reason"] == "max_rounds_exceeded"


@pytest.mark.asyncio
async def test_run_agent_skips_terminal(wire_loop, db):
    wire_loop([{"type": "text", "text": "unused"}, {"type": "end_turn"}])
    agent = await _make_agent(db, status=AgentStatus.done)
    agent.result_md = "already done"
    await db.commit()

    await run_agent(agent.id)

    await db.refresh(agent)
    assert agent.result_md == "already done"  # untouched


@pytest.mark.asyncio
async def test_run_agent_provider_error_fails(wire_loop, db):
    class BoomProvider:
        provider_key = "fake"
        model = "fake-model"

        async def generate_stream(self, messages, tools=None):
            raise RuntimeError("no api key")
            yield  # pragma: no cover — make it an async generator

    import app.agents.runner as rm

    def boom():
        return BoomProvider()

    # Override the provider for this test only.
    orig = rm.get_llm_provider
    rm.get_llm_provider = boom
    try:
        agent = await _make_agent(db)
        await run_agent(agent.id)
    finally:
        rm.get_llm_provider = orig

    await db.refresh(agent)
    assert agent.status == AgentStatus.failed.value
    assert agent.error["reason"] == "run_step_error"


# --- trigger route --------------------------------------------------------


@pytest.mark.asyncio
async def test_run_route_queues_and_schedules(client, db, auth_headers, monkeypatch):
    scheduled: list[int] = []
    # Don't execute the real loop in the route test — just capture the schedule.
    monkeypatch.setattr(routes_mod, "run_agent", lambda agent_id: scheduled.append(agent_id))

    agent = await _make_agent(db)
    resp = await client.post(f"/api/agents/{agent.id}/run", headers=auth_headers)

    assert resp.status_code == 202
    assert resp.json()["status"] == AgentStatus.queued.value
    assert scheduled == [agent.id]


@pytest.mark.asyncio
async def test_run_route_conflict_when_active(client, db, auth_headers, monkeypatch):
    monkeypatch.setattr(routes_mod, "run_agent", lambda agent_id: None)
    agent = await _make_agent(db, status=AgentStatus.working)

    resp = await client.post(f"/api/agents/{agent.id}/run", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_run_route_scopes_to_owner(client, db, auth_headers, monkeypatch):
    monkeypatch.setattr(routes_mod, "run_agent", lambda agent_id: None)
    # Agent owned by a different user.
    agent = AgentTask(title="x", prompt_template="p", allowed_tools=[], user_id=999, tenant_id=1)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    resp = await client.post(f"/api/agents/{agent.id}/run", headers=auth_headers)
    assert resp.status_code == 404
