"""Single-loop agent runner.

One LLM loop drives the whole run — no upfront plan, no per-task hand-off. Same
shape chat already uses and the reference agent SDKs wrap: the model adapts
round to round based on what its tool calls return.

A run instantiates from a definition: config (prompt_template, allowed_tools,
model) is read from the AgentDefinition; all run state lives on the AgentRun.

Flow:

    seed messages = [system, user(prompt_template), user(trigger_input)?]
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
from app.agents.models import AgentDefinition, AgentRun, AgentStatus
from app.agents.runner import ToolNotAllowed, run_step
from app.agents.schemas import RunStepMessage, RunStepRequest
from app.agents.service import transition_status
from app.agents.tools import build_registry, requires_approval
from app.database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


# Hard round cap for the whole run. Enough for fetch -> reason -> output even on
# chatty models; a run that needs more is probably stuck and should fail
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


async def _build_tool_registry(definition: AgentDefinition) -> tuple[ToolRegistry, list[dict]]:
    """Build the (registry, tool_definitions) pair for this run from the
    definition's allowed_tools. Unknown/unimplemented names are ignored."""
    return build_registry(definition.allowed_tools)


async def run_agent(run_id: int) -> None:
    """Drive one run from working -> done/failed via a single LLM loop.

    Opens its own DB session (the triggering request already committed). Errors
    surface as AgentStatus.failed — never raised, since the caller is a
    background task with nothing to catch.
    """
    label = f"run:{run_id}"
    async with AsyncSessionLocal() as session:
        run = await _load(session, run_id)
        if run is None:
            logger.warning("run_agent: %s vanished before start", label)
            return
        if run.status in (AgentStatus.done.value, AgentStatus.failed.value):
            logger.warning("run_agent: %s already terminal (%s) — skipping", label, run.status)
            return

        definition = await session.get(AgentDefinition, run.definition_id)
        if definition is None:
            await _fail(session, run, "definition_missing", f"definition {run.definition_id} not found", -1)
            return

        try:
            await transition_status(session, run=run, new_status=AgentStatus.working)

            registry, tool_definitions = await _build_tool_registry(definition)
            tool_names = [t["name"] for t in tool_definitions]

            if run.messages:
                # Resuming after an approval checkpoint — the approve/reject step
                # appended the tool_results, so continue from the saved
                # conversation rather than reseeding.
                messages = _load_messages(run.messages)
                run.messages = None
                run.pending_action = None
                await session.commit()
            else:
                messages = [
                    RunStepMessage(role="system", content=AGENT_SYSTEM_PROMPT),
                    RunStepMessage(role="user", content=definition.prompt_template),
                ]
                if run.trigger_input:
                    messages.append(RunStepMessage(role="user", content=f"Input:\n{run.trigger_input}"))

            seen_tool_calls: dict[str, str] = {}
            final_text: str | None = None
            # When dedupe fires for every call in a round the model is stuck
            # re-fetching data it already has. Next round we send no tools so it
            # physically can't emit tool_use and must produce text.
            force_no_tools = False

            for round_idx in range(MAX_ROUNDS):
                # Re-fetch each round so an external cancel (status=failed) takes
                # effect promptly.
                run = await _load(session, run_id)
                if run is None:
                    return
                if run.status == AgentStatus.failed.value:
                    logger.info("run_agent: %s cancelled mid-loop", label)
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
                        allowed_tools=definition.allowed_tools,
                        request=RunStepRequest(messages=messages, allowed_tools=step_tool_names),
                        tool_definitions=step_tools,
                        label=label,
                    )
                except ToolNotAllowed as exc:
                    await _fail(session, run, "tool_not_allowed", str(exc), round_idx)
                    return
                except Exception as exc:  # noqa: BLE001
                    logger.exception("run_agent: round %d run_step failed %s", round_idx, label)
                    await _fail(session, run, "run_step_error", f"{type(exc).__name__}: {exc}", round_idx)
                    return

                messages.append(result.assistant_message)

                if result.next_action == "tool_use":
                    if force_no_tools:
                        # We sent tool_definitions=None but the model still
                        # emitted tool_use. Can't progress — break and salvage.
                        logger.warning("run_agent: %s emitted tool_use after no-tools forced", label)
                        break
                    # Human-in-the-loop: if any proposed call mutates external
                    # state, pause the whole round for approval before executing
                    # anything. The assistant tool_use message is already in
                    # `messages`; approve/reject supplies the tool_results.
                    if any(requires_approval(tc.name) for tc in result.tool_calls):
                        await _pause_for_approval(session, run, messages, result.tool_calls)
                        logger.info("run_agent: %s paused for approval (round %d)", label, round_idx)
                        return
                    dispatched, all_deduped = await dispatch_tool_calls(
                        registry,
                        tool_calls=result.tool_calls,
                        seen_tool_calls=seen_tool_calls,
                    )
                    messages.append(RunStepMessage(role="user", content=dispatched))
                    if all_deduped:
                        logger.info("run_agent: %s round=%d all-duplicate — no tools next round", label, round_idx)
                        force_no_tools = True
                    continue

                if result.next_action in ("text", "done"):
                    final_text = extract_text(result.assistant_message.content)
                    break

            if final_text is None:
                await _fail(
                    session,
                    run,
                    "max_rounds_exceeded",
                    f"Run produced no usable final text after {MAX_ROUNDS} rounds.",
                    MAX_ROUNDS,
                )
                return

            await transition_status(session, run=run, new_status=AgentStatus.reporting)
            await transition_status(session, run=run, new_status=AgentStatus.done, result_md=final_text)

        except Exception as exc:  # noqa: BLE001 — background task, we own all errors
            logger.exception("run_agent: unhandled error %s", label)
            await _fail(session, run, "run_agent_error", f"{type(exc).__name__}: {exc}", -1)


# --- helpers --------------------------------------------------------------


def _dump_messages(messages: list[RunStepMessage]) -> list[dict]:
    """Serialize the conversation for persistence across an approval pause."""
    return [m.model_dump() for m in messages]


def _load_messages(data: list[dict]) -> list[RunStepMessage]:
    """Rebuild the conversation saved by `_dump_messages`."""
    return [RunStepMessage(**d) for d in data]


async def _pause_for_approval(
    session: AsyncSession, run: AgentRun, messages: list[RunStepMessage], tool_calls: list
) -> None:
    """Persist the proposed action + conversation and park the run at the
    checkpoint. approve/reject executes the calls and resumes the loop."""
    run.pending_action = {
        "calls": [
            {
                "id": tc.id,
                "name": tc.name,
                "arguments": tc.arguments,
                "requires_approval": requires_approval(tc.name),
            }
            for tc in tool_calls
        ]
    }
    run.messages = _dump_messages(messages)
    await transition_status(session, run=run, new_status=AgentStatus.waiting_approval)


async def _load(session: AsyncSession, run_id: int) -> AgentRun | None:
    result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
    return result.scalar_one_or_none()


async def _fail(session: AsyncSession, run: AgentRun, reason: str, detail: str, step: int) -> None:
    await transition_status(
        session,
        run=run,
        new_status=AgentStatus.failed,
        error={"reason": reason, "detail": detail, "step": step},
    )
