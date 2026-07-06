"""Tests for the single-loop runner (loop.run_agent) over runs + definitions."""

import pytest

from app.agents import loop as loop_mod
from app.agents import runner as runner_mod
from app.agents.loop import run_agent
from app.agents.models import AgentDefinition, AgentRun, AgentStatus


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


async def _make_run(db, prompt="summarize the pipeline", status=AgentStatus.draft, trigger_input=None):
    definition = AgentDefinition(
        name="Lead Intake",
        prompt_template=prompt,
        allowed_tools=[],
        user_id=1,
        tenant_id=1,
    )
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    run = AgentRun(
        definition_id=definition.id,
        user_id=1,
        tenant_id=1,
        status=status.value,
        trigger_input=trigger_input,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@pytest.mark.asyncio
async def test_run_agent_text_only_completes(wire_loop, db):
    wire_loop([{"type": "text", "text": "Pipeline looks healthy."}, {"type": "end_turn"}])
    run = await _make_run(db)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.done.value
    assert run.result_md == "Pipeline looks healthy."
    assert run.started_at is not None
    assert run.completed_at is not None


@pytest.mark.asyncio
async def test_run_agent_uses_trigger_input(wire_loop, db, monkeypatch):
    captured = {}

    class CapturingProvider(FakeProvider):
        async def generate_stream(self, messages, tools=None):
            captured["messages"] = messages
            for event in [{"type": "text", "text": "done"}, {"type": "end_turn"}]:
                yield event

    monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: CapturingProvider([]))
    run = await _make_run(db, trigger_input="Jane from Acme wants a demo")

    await run_agent(run.id)

    # The trigger input is surfaced to the model as a user message.
    contents = [m.get("content", "") for m in captured["messages"]]
    assert any("Jane from Acme" in c for c in contents if isinstance(c, str))


@pytest.mark.asyncio
async def test_run_agent_no_text_fails(wire_loop, db):
    wire_loop([{"type": "end_turn"}])
    run = await _make_run(db)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.failed.value
    assert run.error["reason"] == "max_rounds_exceeded"


@pytest.mark.asyncio
async def test_run_agent_skips_terminal(wire_loop, db):
    wire_loop([{"type": "text", "text": "unused"}, {"type": "end_turn"}])
    run = await _make_run(db, status=AgentStatus.done)
    run.result_md = "already done"
    await db.commit()

    await run_agent(run.id)

    await db.refresh(run)
    assert run.result_md == "already done"  # untouched


@pytest.mark.asyncio
async def test_run_agent_provider_error_fails(wire_loop, db, monkeypatch):
    class BoomProvider:
        provider_key = "fake"
        model = "fake-model"

        async def generate_stream(self, messages, tools=None):
            raise RuntimeError("no api key")
            yield  # pragma: no cover — make it an async generator

    monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: BoomProvider())
    run = await _make_run(db)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.failed.value
    assert run.error["reason"] == "run_step_error"
