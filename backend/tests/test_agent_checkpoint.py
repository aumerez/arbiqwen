"""Tests for the human-in-the-loop checkpoint: the loop pauses on an
approval-required tool call and resumes from the saved conversation."""

import pytest

from app.agents import loop as loop_mod
from app.agents import runner as runner_mod
from app.agents.loop import run_agent
from app.agents.models import AgentDefinition, AgentRun, AgentStatus


class FakeProvider:
    provider_key = "fake"
    model = "fake-model"

    def __init__(self, rounds):
        self._rounds = list(rounds)

    async def generate_stream(self, messages, tools=None):
        self.last_messages = messages
        for e in self._rounds.pop(0):
            yield e


@pytest.fixture
def wire(monkeypatch, session_factory):
    monkeypatch.setattr(loop_mod, "AsyncSessionLocal", session_factory)

    def set_provider(provider):
        monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: provider)

    return set_provider


async def _make_run(db, *, allowed_tools, status=AgentStatus.draft, messages=None):
    definition = AgentDefinition(
        name="Lead Intake",
        prompt_template="Handle the inquiry",
        allowed_tools=allowed_tools,
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
        messages=messages,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@pytest.mark.asyncio
async def test_run_pauses_on_approval_required_tool(wire, db):
    # Model proposes a write (plane_create_task) → run must pause, not execute.
    wire(
        FakeProvider([[{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {"name": "Call Acme"}}]])
    )
    run = await _make_run(db, allowed_tools=["plane_create_task"])

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.waiting_approval.value
    assert run.pending_action["calls"][0]["name"] == "plane_create_task"
    assert run.pending_action["calls"][0]["arguments"] == {"name": "Call Acme"}
    assert run.pending_action["calls"][0]["requires_approval"] is True
    # Conversation persisted for resume, ending with the assistant tool_use.
    assert run.messages is not None
    assert run.messages[-1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_read_tool_does_not_pause(wire, db):
    # A read-only tool runs without pausing; then the model answers.
    wire(
        FakeProvider(
            [
                [{"type": "tool_use", "id": "c1", "name": "plane_list_tasks", "input": {}}],
                [{"type": "text", "text": "There are 3 open tasks."}, {"type": "end_turn"}],
            ]
        )
    )
    # plane_list_tasks will error (no Plane env) but that's a normal tool error,
    # not a pause — the run still completes.
    run = await _make_run(db, allowed_tools=["plane_list_tasks"])

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.done.value
    assert run.pending_action is None


@pytest.mark.asyncio
async def test_resume_from_saved_conversation_completes(wire, db):
    # Simulate the state right after approval: conversation saved, tool_result
    # appended, status working. run_agent should resume and finish.
    saved = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Handle the inquiry"},
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {"name": "Call Acme"}}],
        },
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "created OPS-9"}]},
    ]
    provider = FakeProvider([[{"type": "text", "text": "Done — created task OPS-9."}, {"type": "end_turn"}]])
    wire(provider)
    run = await _make_run(db, allowed_tools=["plane_create_task"], status=AgentStatus.working, messages=saved)

    await run_agent(run.id)

    await db.refresh(run)
    assert run.status == AgentStatus.done.value
    assert "OPS-9" in run.result_md
    # Checkpoint state cleared on resume.
    assert run.messages is None
    assert run.pending_action is None
    # The model saw the full saved conversation on resume.
    assert provider.last_messages[0]["role"] == "system"
    assert any("created OPS-9" in str(m.get("content")) for m in provider.last_messages)
