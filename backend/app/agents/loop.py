"""Single-loop agent runner.

One LLM loop drives the whole run — no upfront plan, no per-task hand-off. Same
shape chat already uses and the reference agent SDKs wrap: the model adapts
round to round based on what its tool calls return.

Flow:

    seed messages = [system, user(prompt_template)]
    loop up to MAX_ROUNDS:
        run_step  -> one LLM round
        if next_action in (text, done): return final text
        if next_action == tool_use:
            dispatch tool_calls (dedupe inside), append tool_result message
            if every call was a duplicate -> force a no-tools round next

Guardrail: this is intentionally a SINGLE loop — no orchestrator/supervisor,
no sub-agent spawning. Genuine multi-step work happens via chained tool calls
in one loop. The tool registry is empty in this PR (text-only reasoning);
feat/agent-tools populates it with Twenty CRM + Plane.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents._runtime import ToolRegistry, dispatch_tool_calls, extract_text
from app.agents.models import AgentStatus, AgentTask
from app.agents.runner import ToolNotAllowed, run_step
from app.agents.schemas import RunStepMessage, RunStepRequest
from app.agents.service import transition_status
from app.database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


# Hard round cap for the whole run. Enough for fetch -> reason -> output even on
# chatty models; an agent that needs more is probably stuck and should fail
# cleanly rather than burn tokens.
MAX_ROUNDS = 10


AGENT_SYSTEM_PROMPT = """You are an autonomous agent executing a task in the background. The user is NOT available to answer follow-up questions — they will only see your final text output.

Rules:
1. DO the work yourself. Use the tools available to gather anything you need.
2. NEVER ask the user for information or clarification. If you need context, find it via tools.
3. When you have enough data to answer, STOP calling tools and write your final answer as text.
4. If data is genuinely unavailable after real tool attempts, say so plainly in your final answer.
5. Identical repeat tool calls are blocked by the platform — looping wastes tokens without unlocking new data. Use what you have and answer.
6. Your final text IS the deliverable the user receives. Make it dense and useful.
7. Do NOT use emojis anywhere in your output. Plain text only. Markdown formatting (headings, lists, code blocks) is fine; emojis are not.

Match the language and format the user asked for in the task prompt."""


async def _build_tool_registry(agent: AgentTask) -> tuple[ToolRegistry, list[dict]]:
    """Build the (registry, tool_definitions) pair for this run.

    Empty in this PR — the loop runs text-only reasoning. feat/agent-tools
    returns the agent's allowed Twenty/Plane callables plus their schemas here,
    with no other change to the loop.
    """
    return {}, []


async def run_agent(agent_id: int) -> None:
    """Drive one agent from working -> done/failed via a single LLM loop.

    Opens its own DB session (the triggering request already committed). Errors
    surface as AgentStatus.failed — never raised, since the caller is a
    background task with nothing to catch.
    """
    async with AsyncSessionLocal() as session:
        agent = await _load(session, agent_id)
        if agent is None:
            logger.warning("run_agent: agent=%s vanished before start", agent_id)
            return
        if agent.status in (AgentStatus.done.value, AgentStatus.failed.value):
            logger.warning("run_agent: agent=%s already terminal (%s) — skipping", agent_id, agent.status)
            return

        try:
            await transition_status(session, agent=agent, new_status=AgentStatus.working)

            registry, tool_definitions = await _build_tool_registry(agent)
            tool_names = [t["name"] for t in tool_definitions]

            messages: list[RunStepMessage] = [
                RunStepMessage(role="system", content=AGENT_SYSTEM_PROMPT),
                RunStepMessage(role="user", content=agent.prompt_template),
            ]

            seen_tool_calls: dict[str, str] = {}
            final_text: str | None = None
            # When dedupe fires for every call in a round the model is stuck
            # re-fetching data it already has. Next round we send no tools so it
            # physically can't emit tool_use and must produce text.
            force_no_tools = False

            for round_idx in range(MAX_ROUNDS):
                # Re-fetch each round so an external cancel (status=failed) takes
                # effect promptly.
                agent = await _load(session, agent_id)
                if agent is None:
                    return
                if agent.status == AgentStatus.failed.value:
                    logger.info("run_agent: agent=%s cancelled mid-loop", agent_id)
                    return

                if force_no_tools:
                    step_tools: list[dict] | None = None
                    step_tool_names: list[str] = []
                    messages.append(
                        RunStepMessage(
                            role="user",
                            content=(
                                "[SYSTEM] You have gathered enough data. Do NOT call any "
                                "tools this round — write the final answer now using what "
                                "you already have."
                            ),
                        )
                    )
                else:
                    step_tools = tool_definitions or None
                    step_tool_names = tool_names

                try:
                    result = await run_step(
                        agent=agent,
                        request=RunStepRequest(messages=messages, allowed_tools=step_tool_names),
                        tool_definitions=step_tools,
                    )
                except ToolNotAllowed as exc:
                    await _fail(session, agent, "tool_not_allowed", str(exc), round_idx)
                    return
                except Exception as exc:  # noqa: BLE001
                    logger.exception("run_agent: round %d run_step failed agent=%s", round_idx, agent_id)
                    await _fail(session, agent, "run_step_error", f"{type(exc).__name__}: {exc}", round_idx)
                    return

                messages.append(result.assistant_message)

                if result.next_action == "tool_use":
                    if force_no_tools:
                        # We sent tool_definitions=None but the model still
                        # emitted tool_use. Can't progress — break and salvage.
                        logger.warning("run_agent: agent=%s emitted tool_use after no-tools forced", agent_id)
                        break
                    dispatched, all_deduped = await dispatch_tool_calls(
                        registry,
                        tool_calls=result.tool_calls,
                        seen_tool_calls=seen_tool_calls,
                    )
                    messages.append(RunStepMessage(role="user", content=dispatched))
                    if all_deduped:
                        logger.info(
                            "run_agent: agent=%s round=%d all-duplicate — no tools next round", agent_id, round_idx
                        )
                        force_no_tools = True
                    continue

                if result.next_action in ("text", "done"):
                    final_text = extract_text(result.assistant_message.content)
                    break

            if final_text is None:
                await _fail(
                    session,
                    agent,
                    "max_rounds_exceeded",
                    f"Agent produced no usable final text after {MAX_ROUNDS} rounds.",
                    MAX_ROUNDS,
                )
                return

            await transition_status(session, agent=agent, new_status=AgentStatus.reporting)
            await transition_status(session, agent=agent, new_status=AgentStatus.done, result_md=final_text)

        except Exception as exc:  # noqa: BLE001 — background task, we own all errors
            logger.exception("run_agent: unhandled error agent=%s", agent_id)
            await _fail(session, agent, "run_agent_error", f"{type(exc).__name__}: {exc}", -1)


# --- helpers --------------------------------------------------------------


async def _load(session: AsyncSession, agent_id: int) -> AgentTask | None:
    result = await session.execute(select(AgentTask).where(AgentTask.id == agent_id))
    return result.scalar_one_or_none()


async def _fail(session: AsyncSession, agent: AgentTask, reason: str, detail: str, step: int) -> None:
    await transition_status(
        session,
        agent=agent,
        new_status=AgentStatus.failed,
        error={"reason": reason, "detail": detail, "step": step},
    )
