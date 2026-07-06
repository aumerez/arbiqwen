"""Unit tests for the agent run-step primitives (runner, _runtime, service)."""

import pytest

from app.agents import runner as runner_mod
from app.agents._runtime import _dedupe_key, _format_tool_result, dispatch_tool_calls, extract_text
from app.agents.models import AgentStatus, AgentTask
from app.agents.runner import ToolNotAllowed, run_step
from app.agents.schemas import RunStepRequest, RunStepToolCall
from app.agents.service import transition_status


class FakeProvider:
    """Yields a scripted event stream from generate_stream."""

    provider_key = "fake"
    model = "fake-model"

    def __init__(self, events):
        self._events = events

    async def generate_stream(self, messages, tools=None):
        self.seen_tools = tools
        for event in self._events:
            yield event


def _use_provider(monkeypatch, events):
    provider = FakeProvider(events)
    monkeypatch.setattr(runner_mod, "get_llm_provider", lambda: provider)
    return provider


def _req(text="do the thing"):
    return RunStepRequest(messages=[{"role": "user", "content": text}])


@pytest.mark.asyncio
async def test_run_step_text_only(monkeypatch):
    _use_provider(
        monkeypatch,
        [
            {"type": "text", "text": "hello "},
            {"type": "text", "text": "world"},
            {"type": "end_turn"},
            {"type": "usage", "input_tokens": 5, "output_tokens": 3},
        ],
    )
    agent = AgentTask(id=1, allowed_tools=[])
    resp = await run_step(agent=agent, request=_req())

    assert resp.next_action == "done"
    assert resp.assistant_message.content == "hello world"
    assert resp.usage.input_tokens == 5
    assert resp.usage.output_tokens == 3
    assert resp.usage.provider_key == "fake"
    assert resp.usage.model_id == "fake-model"


@pytest.mark.asyncio
async def test_run_step_text_without_end_turn_is_text_action(monkeypatch):
    _use_provider(monkeypatch, [{"type": "text", "text": "partial"}])
    agent = AgentTask(id=1, allowed_tools=[])
    resp = await run_step(agent=agent, request=_req())
    assert resp.next_action == "text"


@pytest.mark.asyncio
async def test_run_step_allowed_tool_call(monkeypatch):
    _use_provider(
        monkeypatch,
        [{"type": "tool_use", "id": "t1", "name": "search", "input": {"q": "acme"}}],
    )
    agent = AgentTask(id=1, allowed_tools=["search"])
    resp = await run_step(agent=agent, request=_req())

    assert resp.next_action == "tool_use"
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "search"
    assert resp.tool_calls[0].arguments == {"q": "acme"}
    # Assistant message carries the tool_use in a content block.
    assert any(b["type"] == "tool_use" for b in resp.assistant_message.content)


@pytest.mark.asyncio
async def test_run_step_disallowed_tool_raises(monkeypatch):
    _use_provider(
        monkeypatch,
        [{"type": "tool_use", "id": "t1", "name": "delete_everything", "input": {}}],
    )
    agent = AgentTask(id=1, allowed_tools=["search"])
    with pytest.raises(ToolNotAllowed):
        await run_step(agent=agent, request=_req())


@pytest.mark.asyncio
async def test_run_step_narrowing_cannot_widen(monkeypatch):
    # Request asks for a tool the agent doesn't have — it's dropped, so the
    # model calling it still trips the whitelist.
    _use_provider(
        monkeypatch,
        [{"type": "tool_use", "id": "t1", "name": "extra", "input": {}}],
    )
    agent = AgentTask(id=1, allowed_tools=["search"])
    req = RunStepRequest(messages=[{"role": "user", "content": "x"}], allowed_tools=["search", "extra"])
    with pytest.raises(ToolNotAllowed):
        await run_step(agent=agent, request=req)


# --- _runtime -------------------------------------------------------------


def test_dedupe_key_is_order_independent():
    assert _dedupe_key("t", {"a": 1, "b": 2}) == _dedupe_key("t", {"b": 2, "a": 1})


def test_format_tool_result_shapes():
    assert _format_tool_result({"text": "hi"}) == "hi"
    assert "acme" in _format_tool_result({"name": "acme"})
    assert _format_tool_result(42) == "42"


def test_extract_text_from_blocks():
    blocks = [{"type": "text", "text": "answer"}, {"type": "tool_use", "id": "x"}]
    assert extract_text(blocks) == "answer"
    assert extract_text("  plain  ") == "plain"
    assert extract_text(None) is None


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_is_error():
    calls = [RunStepToolCall(id="t1", name="ghost", arguments={})]
    blocks, all_deduped = await dispatch_tool_calls({}, tool_calls=calls, seen_tool_calls={})
    assert blocks[0]["is_error"] is True
    assert all_deduped is False


@pytest.mark.asyncio
async def test_dispatch_runs_and_caches():
    async def echo(args):
        return {"text": f"echo:{args['v']}"}

    seen: dict[str, str] = {}
    calls = [RunStepToolCall(id="t1", name="echo", arguments={"v": "hi"})]
    blocks, all_deduped = await dispatch_tool_calls({"echo": echo}, tool_calls=calls, seen_tool_calls=seen)

    assert blocks[0]["content"] == "echo:hi"
    assert all_deduped is False
    assert seen  # result cached for dedupe


@pytest.mark.asyncio
async def test_dispatch_dedupes_repeat_call():
    async def echo(args):
        return {"text": "fresh"}

    seen = {_dedupe_key("echo", {"v": "hi"}): "cached-result"}
    calls = [RunStepToolCall(id="t2", name="echo", arguments={"v": "hi"})]
    blocks, all_deduped = await dispatch_tool_calls({"echo": echo}, tool_calls=calls, seen_tool_calls=seen)

    assert all_deduped is True
    assert "DUPLICATE" in blocks[0]["content"]
    assert "cached-result" in blocks[0]["content"]


@pytest.mark.asyncio
async def test_dispatch_tool_error_not_cached():
    async def boom(args):
        raise RuntimeError("kaboom")

    seen: dict[str, str] = {}
    calls = [RunStepToolCall(id="t1", name="boom", arguments={})]
    blocks, _ = await dispatch_tool_calls({"boom": boom}, tool_calls=calls, seen_tool_calls=seen)
    assert blocks[0]["is_error"] is True
    assert seen == {}


# --- service --------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_status_stamps_timestamps(db):
    agent = AgentTask(title="t", prompt_template="p", allowed_tools=[], user_id=1, tenant_id=1)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    await transition_status(db, agent=agent, new_status=AgentStatus.working)
    assert agent.status == AgentStatus.working.value
    assert agent.started_at is not None
    assert agent.completed_at is None

    await transition_status(db, agent=agent, new_status=AgentStatus.done, result_md="final answer")
    assert agent.status == AgentStatus.done.value
    assert agent.completed_at is not None
    assert agent.result_md == "final answer"


@pytest.mark.asyncio
async def test_transition_status_records_error(db):
    agent = AgentTask(title="t", prompt_template="p", allowed_tools=[], user_id=1, tenant_id=1)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    await transition_status(db, agent=agent, new_status=AgentStatus.failed, error={"reason": "boom"})
    assert agent.status == AgentStatus.failed.value
    assert agent.error == {"reason": "boom"}
    assert agent.completed_at is not None
