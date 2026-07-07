"""Unit tests for the Anthropic->OpenAI message/tool adapters used to run agent
tool rounds on OpenAI-compatible providers (DashScope/Qwen)."""

import json

import pytest

from app.llm.provider import (
    AlibabaProvider,
    _anthropic_messages_to_openai,
    _anthropic_tools_to_openai,
)


def test_plain_messages_pass_through():
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    assert _anthropic_messages_to_openai(msgs) == msgs


def test_assistant_tool_use_becomes_tool_calls():
    msgs = [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "calling"},
                {"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {"name": "Fix pump"}},
            ],
        }
    ]
    out = _anthropic_messages_to_openai(msgs)
    assert out[0]["role"] == "assistant"
    assert out[0]["content"] == "calling"
    tc = out[0]["tool_calls"][0]
    assert tc["id"] == "c1"
    assert tc["type"] == "function"
    assert tc["function"]["name"] == "plane_create_task"
    assert json.loads(tc["function"]["arguments"]) == {"name": "Fix pump"}


def test_tool_result_becomes_tool_message():
    msgs = [
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "created OPS-9"}],
        }
    ]
    out = _anthropic_messages_to_openai(msgs)
    assert out == [{"role": "tool", "tool_call_id": "c1", "content": "created OPS-9"}]


def test_tool_result_list_content_flattened():
    msgs = [
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "c1", "content": [{"type": "text", "text": "ok"}]}],
        }
    ]
    out = _anthropic_messages_to_openai(msgs)
    assert out[0]["content"] == "ok"


def test_assistant_tool_use_only_has_null_content():
    msgs = [{"role": "assistant", "content": [{"type": "tool_use", "id": "c1", "name": "t", "input": {}}]}]
    out = _anthropic_messages_to_openai(msgs)
    assert out[0]["content"] is None
    assert out[0]["tool_calls"][0]["function"]["name"] == "t"


def test_tools_converted_to_openai_function_shape():
    tools = [
        {
            "name": "plane_create_task",
            "description": "Create a task",
            "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            "_internal": "dropped",
        }
    ]
    out = _anthropic_tools_to_openai(tools)
    assert out[0]["type"] == "function"
    fn = out[0]["function"]
    assert fn["name"] == "plane_create_task"
    assert fn["parameters"]["required"] == ["name"]
    assert "_internal" not in json.dumps(out[0])


def test_tools_missing_input_schema_gets_empty_object():
    out = _anthropic_tools_to_openai([{"name": "t", "description": "d"}])
    assert out[0]["function"]["parameters"] == {"type": "object", "properties": {}}


@pytest.mark.asyncio
async def test_alibaba_stream_sends_converted_payload(monkeypatch):
    """The provider converts messages + tools before hitting the OpenAI client."""
    captured = {}

    class FakeChunk:
        usage = None
        choices = []

    class FakeStream:
        def __aiter__(self):
            async def gen():
                yield FakeChunk()

            return gen()

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                async def create(**kwargs):
                    captured.update(kwargs)
                    return FakeStream()

    provider = AlibabaProvider(api_key="x", base_url="http://x", model="qwen")
    monkeypatch.setattr(type(provider), "client", property(lambda self: FakeClient()))

    messages = [
        {"role": "user", "content": "make a task"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "done"}]},
    ]
    tools = [{"name": "plane_create_task", "description": "d", "input_schema": {"type": "object"}}]

    async for _ in provider.generate_stream(messages=messages, tools=tools):
        pass

    roles = [m["role"] for m in captured["messages"]]
    assert roles == ["user", "assistant", "tool"]
    assert captured["messages"][1]["tool_calls"][0]["function"]["name"] == "plane_create_task"
    assert captured["tools"][0]["type"] == "function"
