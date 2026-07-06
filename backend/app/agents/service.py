"""Agent run lifecycle helpers.

Run progress is logged via status transitions on the `agent_runs` row. A
dedicated step-event log is deferred. `transition_status` is the single writer
of run state so timestamps stay consistent across the loop and the trigger
route.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentRun, AgentStatus


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
    - entering `done`/`failed` sets `completed_at`;
    - `result_md`/`error` are written when provided.
    Commits before returning so a background run persists each step even if a
    later step raises.
    """
    now = datetime.now(UTC)
    run.status = new_status.value

    if new_status is AgentStatus.working and run.started_at is None:
        run.started_at = now
    if new_status in (AgentStatus.done, AgentStatus.failed):
        run.completed_at = now
    if result_md is not None:
        run.result_md = result_md
    if error is not None:
        run.error = error

    await session.commit()
    await session.refresh(run)
    return run
