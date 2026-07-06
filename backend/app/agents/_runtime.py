"""Shared agent-runtime helpers: tool dispatch, result formatting, dedupe.

The loop (loop.py) owns iteration; this module owns the mechanics of turning a
round's `tool_calls` into `tool_result` blocks. Tools resolve against a
registry — a plain ``{name: async fn(arguments) -> result}`` map — that the
loop builds per run. In this PR the registry is empty (text-only reasoning);
PR D (feat/agent-tools) populates it with Twenty CRM + Plane callables. The
dispatch, dedupe, and error-shaping logic here is already the shape those
tools plug into, so D adds tools without touching the loop.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.schemas import RunStepToolCall

logger = logging.getLogger(__name__)

# A tool is an async callable taking the parsed arguments dict and returning a
# result (str, or a dict — see _format_tool_result for the shapes rendered).
ToolFn = Callable[[dict], Awaitable[Any]]
ToolRegistry = dict[str, ToolFn]

# Safety cap on rendered tool-result text so one huge result can't blow up the
# conversation history.
_TOOL_RESULT_MAX_CHARS = 16000


def _dedupe_key(tool_name: str, tool_input: dict) -> str:
    """Normalized (name + canonical-JSON-input) key for cross-round dedupe."""
    try:
        normalized = json.dumps(tool_input, sort_keys=True, default=str)
    except (TypeError, ValueError):
        normalized = repr(tool_input)
    return f"{tool_name}::{normalized}"


def _format_tool_result(result: Any) -> str:
    """Render a tool result as the text the LLM will see.

    A dict carrying a ``text`` key is passed through (skill/meta shape); other
    dicts are JSON-dumped; everything else falls through to ``str()``. All
    capped at _TOOL_RESULT_MAX_CHARS.
    """
    if isinstance(result, dict) and "text" in result:
        text = result.get("text") or ""
        return str(text)[:_TOOL_RESULT_MAX_CHARS]
    if isinstance(result, dict):
        try:
            rendered = json.dumps(result, indent=2, default=str)
        except (TypeError, ValueError):
            rendered = str(result)
        return rendered[:_TOOL_RESULT_MAX_CHARS]
    return str(result)[:_TOOL_RESULT_MAX_CHARS]


async def dispatch_tool_calls(
    registry: ToolRegistry,
    *,
    tool_calls: list[RunStepToolCall],
    seen_tool_calls: dict[str, str],
) -> tuple[list[dict], bool]:
    """Execute each tool call and return (tool_result blocks, all_deduped).

    `all_deduped` is True iff EVERY call this round was a duplicate that got
    short-circuited — the loop uses that to force a no-tools round next (some
    models ignore the dedupe notice and keep re-fetching).

    Individual tool errors come back as `is_error: true` blocks so the model
    sees the failure and can adapt rather than crashing the run. An unknown
    tool (not in the registry) is one such error.
    """
    results: list[dict] = []
    all_deduped = True
    for tc in tool_calls:
        block: dict = {"type": "tool_result", "tool_use_id": tc.id}

        dedupe_key = _dedupe_key(tc.name, tc.arguments)
        if dedupe_key in seen_tool_calls:
            logger.info("agent tool dedupe: short-circuiting duplicate call tool=%s", tc.name)
            block["content"] = (
                "[DUPLICATE — this exact call already ran earlier in this run. The prior "
                "result is below. Do NOT re-call this tool. Use what you have and write "
                "your final answer now.]\n\n" + seen_tool_calls[dedupe_key]
            )
            results.append(block)
            continue

        all_deduped = False  # at least one call did real work

        fn = registry.get(tc.name)
        if fn is None:
            block["content"] = f"Tool '{tc.name}' is not available to this agent."
            block["is_error"] = True
            results.append(block)
            continue

        try:
            result = await fn(tc.arguments)
            content = _format_tool_result(result)
            is_error = isinstance(result, dict) and result.get("error") is not None
            block["content"] = content
            if is_error:
                block["is_error"] = True
            else:
                # Only cache successful results — an error shouldn't block a
                # retry with different args.
                seen_tool_calls[dedupe_key] = content
        except Exception as exc:  # noqa: BLE001 — surface to the model, don't crash the run
            logger.exception("agent tool dispatch failed: tool=%s", tc.name)
            block["content"] = f"Tool '{tc.name}' errored: {type(exc).__name__}: {exc}"
            block["is_error"] = True

        results.append(block)

    return results, all_deduped


def extract_text(content: str | list[dict] | None) -> str | None:
    """Pull the plain text out of an assistant message's content.

    Content is a plain string when no tools were involved, or a list of
    Anthropic blocks when they were — in which case the answer is the text
    block(s). Returns None if there's no usable text.
    """
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip() or None
    parts = [str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text"]
    joined = "\n".join(p for p in parts if p).strip()
    return joined or None
