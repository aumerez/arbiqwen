"""Agent run lifecycle helpers.

PR B logs run progress via status transitions on the `agent_tasks` row only —
a dedicated step-event log (agent_steps) is deferred to PR C where the schema
is split into definitions + runs. `transition_status` is the single writer of
run state so timestamps stay consistent across the loop and the trigger route.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentStatus, AgentTask


async def transition_status(
    session: AsyncSession,
    *,
    agent: AgentTask,
    new_status: AgentStatus,
    error: dict | None = None,
    result_md: str | None = None,
) -> AgentTask:
    """Move an agent to `new_status`, stamping timestamps and result/error.

    - entering `working` sets `started_at` (once);
    - entering `done`/`failed` sets `completed_at`;
    - `result_md`/`error` are written when provided.
    Commits before returning so a background run persists each step even if a
    later step raises.
    """
    now = datetime.now(UTC)
    agent.status = new_status.value

    if new_status is AgentStatus.working and agent.started_at is None:
        agent.started_at = now
    if new_status in (AgentStatus.done, AgentStatus.failed):
        agent.completed_at = now
    if result_md is not None:
        agent.result_md = result_md
    if error is not None:
        agent.error = error

    await session.commit()
    await session.refresh(agent)
    return agent
