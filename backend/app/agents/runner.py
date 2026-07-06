"""Stateless run-step primitive for agent tasks.

One call = one LLM round. The loop (loop.py) iterates over this; keeping the
loop OUT of this function is deliberate — the runner does exactly one thing:
turn a message list into the next LLM turn, enforcing the per-agent tool
whitelist server-side so a caller (or the model) can never widen the agent's
stored `allowed_tools`.

Tool EXECUTION is not this function's job. The runner returns any `tool_calls`
the model emitted; the loop dispatches them (via _runtime) and feeds results
back as a `tool_result` message on the next call.
"""

from __future__ import annotations

import logging

from app.agents.schemas import (
    RunStepMessage,
    RunStepRequest,
    RunStepResponse,
    RunStepToolCall,
    RunStepUsage,
)
from app.llm import get_llm_provider

logger = logging.getLogger(__name__)


class ToolNotAllowed(Exception):
    """The LLM tried to call a tool outside the agent's whitelist.

    The loop catches this, marks the run failed, and surfaces a structured
    error. Separate from generic exceptions so logs can tell a policy
    violation apart from a bug.
    """


def _resolve_allowed_tools(allowed_tools: list[str], requested: list[str] | None) -> list[str]:
    """Intersect the caller's requested subset with the definition's whitelist.

    Server truth is the definition's `allowed_tools`. Callers can only narrow
    it; an attempt to widen silently drops the extras (the common case is a
    client re-sending the stored whitelist verbatim, which is fine).
    """
    stored = set(allowed_tools or [])
    if requested is None:
        return list(stored)
    return [name for name in requested if name in stored]


def _filter_tool_definitions(tool_defs: list[dict], allowed_names: list[str]) -> list[dict]:
    """Keep only tool definitions whose name is in `allowed_names`.

    The caller may pass more tools than a given agent is allowed; this is the
    per-agent narrowing. An empty result is legal (LLM-only round).
    """
    allowed_set = set(allowed_names)
    return [t for t in tool_defs if t.get("name") in allowed_set]


def _messages_to_dicts(messages: list[RunStepMessage]) -> list[dict]:
    """Convert pydantic message models to the plain dicts the provider expects."""
    out: list[dict] = []
    for m in messages:
        d: dict = {"role": m.role}
        if m.content is not None:
            d["content"] = m.content
        out.append(d)
    return out


async def run_step(
    *,
    allowed_tools: list[str],
    request: RunStepRequest,
    tool_definitions: list[dict] | None = None,
    label: str = "agent",
) -> RunStepResponse:
    """Run one LLM round.

    Args:
        allowed_tools: The definition's tool whitelist (server truth).
        request: Messages + optional narrowing of allowed_tools.
        tool_definitions: Tool schemas the LLM may see. Filtered by the
            whitelist before sending. None/empty → text-only round.
        label: Identifier for logs/errors (e.g. ``run:42``).

    Returns:
        RunStepResponse with the assistant message + any tool_calls + usage.
    """
    allowed_names = _resolve_allowed_tools(allowed_tools, request.allowed_tools)
    filtered_tools = (_filter_tool_definitions(tool_definitions, allowed_names) if tool_definitions else []) or None

    provider = get_llm_provider()
    llm_messages = _messages_to_dicts(request.messages)

    text_chunks: list[str] = []
    tool_calls: list[RunStepToolCall] = []
    usage = RunStepUsage(provider_key=provider.provider_key, model_id=getattr(provider, "model", None))
    finish_reason: str | None = None

    async for event in provider.generate_stream(messages=llm_messages, tools=filtered_tools):
        etype = event.get("type")
        if etype == "text":
            text_chunks.append(event.get("text", ""))
        elif etype == "tool_use":
            name = event.get("name", "")
            # Server-side whitelist enforcement — the model can't bypass the
            # per-agent narrowing even if it hallucinates a tool name.
            if name not in allowed_names:
                raise ToolNotAllowed(f"{label} tried to call '{name}', not in allowed_tools={allowed_names}")
            arguments = event.get("input") or {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append(RunStepToolCall(id=event.get("id", ""), name=name, arguments=arguments))
        elif etype == "usage":
            usage.input_tokens = int(event.get("input_tokens", 0) or 0)
            usage.output_tokens = int(event.get("output_tokens", 0) or 0)
        elif etype == "end_turn":
            finish_reason = "end_turn"

    assistant_text = "".join(text_chunks) or None

    # Build the assistant message in the Anthropic-native content-block shape.
    # tool_use goes into a structured content array (not a parallel field) so
    # the next round's tool_result blocks line up with it.
    if tool_calls:
        blocks: list[dict] = []
        if assistant_text:
            blocks.append({"type": "text", "text": assistant_text})
        for tc in tool_calls:
            blocks.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments})
        assistant_message = RunStepMessage(role="assistant", content=blocks)
    else:
        assistant_message = RunStepMessage(role="assistant", content=assistant_text)

    if tool_calls:
        next_action = "tool_use"
    elif finish_reason == "end_turn":
        next_action = "done"
    else:
        next_action = "text"

    return RunStepResponse(
        next_action=next_action,
        assistant_message=assistant_message,
        tool_calls=tool_calls,
        usage=usage,
    )
