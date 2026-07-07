"""Agent run lifecycle helpers.

Run progress is logged via status transitions on the `agent_runs` row. A
dedicated step-event log is deferred. `transition_status` is the single writer
of run state so timestamps stay consistent across the loop and the trigger
route.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents._runtime import dispatch_tool_calls
from app.agents.models import AgentDefinition, AgentRun, AgentStatus
from app.agents.schemas import RunStepToolCall
from app.agents.tools import build_registry

_TERMINAL = (AgentStatus.done, AgentStatus.failed, AgentStatus.rejected)


async def transition_status(
    session: AsyncSession,
    *,
    run: AgentRun,
    new_status: AgentStatus,
    error: dict | None = None,
    result_md: str | None = None,
) -> AgentRun:
    """Move a run to `new_status`, stamping timestamps and result/error.

    - entering `working` sets `started_at` (once);
    - entering a terminal status (`done`/`failed`/`rejected`) sets `completed_at`;
    - `result_md`/`error` are written when provided.
    Commits before returning so a background run persists each step even if a
    later step raises.
    """
    now = datetime.now(UTC)
    run.status = new_status.value

    if new_status is AgentStatus.working and run.started_at is None:
        run.started_at = now
    if new_status in _TERMINAL:
        run.completed_at = now
    if result_md is not None:
        run.result_md = result_md
    if error is not None:
        run.error = error

    await session.commit()
    await session.refresh(run)
    return run


async def apply_approval(
    session: AsyncSession,
    *,
    run: AgentRun,
    definition: AgentDefinition,
    edited_input: dict | None = None,
) -> AgentRun:
    """Execute the checkpoint's pending tool calls and stage the run to resume.

    Runs each proposed call (approval-required ones optionally patched with
    `edited_input`), appends the tool_results to the saved conversation, clears
    the checkpoint, and sets status back to `working`. The caller schedules
    run_agent to continue the loop.
    """
    registry, _ = build_registry(definition.allowed_tools)
    calls: list[RunStepToolCall] = []
    for c in (run.pending_action or {}).get("calls", []):
        args = dict(c.get("arguments") or {})
        if c.get("requires_approval") and edited_input:
            args.update(edited_input)
        calls.append(RunStepToolCall(id=c["id"], name=c["name"], arguments=args))

    blocks, _ = await dispatch_tool_calls(registry, tool_calls=calls, seen_tool_calls={})

    messages = list(run.messages or [])
    messages.append({"role": "user", "content": blocks})
    run.messages = messages
    run.pending_action = None
    return await transition_status(session, run=run, new_status=AgentStatus.working)


async def apply_rejection(session: AsyncSession, *, run: AgentRun, reason: str | None = None) -> AgentRun:
    """Reject the pending action: terminate the run without executing it."""
    run.messages = None
    detail = f"Action rejected by the reviewer{f': {reason}' if reason else ''}. No changes were made."
    return await transition_status(session, run=run, new_status=AgentStatus.rejected, result_md=detail)
