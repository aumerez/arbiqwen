"""Agent memory — write a memory at run end, recall relevant memories at run start.

Design:
  save_memory  — summarise what happened (input + outcome), embed it, upsert to
                 Qdrant, persist a relational row in agent_memories.
  recall_memories — embed the current trigger_input, query Qdrant, return the
                    top-k most relevant past outcomes as formatted text.

Both operations are guarded: missing embedding key or unreachable Qdrant returns
None/[] rather than crashing the run.  The agent loop degrades gracefully when
the memory store is unconfigured.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentMemory, AgentRun
from app.config import settings

logger = logging.getLogger(__name__)

_MEMORY_COLLECTION = "agent_memories"


def _is_configured() -> bool:
    if settings.EMBEDDING_PROVIDER == "dashscope":
        return bool(settings.DASHSCOPE_API_KEY)
    return bool(settings.OPENAI_API_KEY)


def _build_summary(run: AgentRun) -> str:
    parts: list[str] = []
    if run.trigger_input:
        parts.append(f"Input: {run.trigger_input[:500]}")
    if run.result_md:
        parts.append(f"Outcome: {run.result_md[:800]}")
    return "\n".join(parts) or "No summary available."


async def save_memory(session: AsyncSession, *, run: AgentRun) -> AgentMemory | None:
    """Write a memory record for a completed run.

    Embeds the summary, upserts to Qdrant, and persists the relational row.
    Returns None (silently) when the embedding store is unconfigured.
    """
    if not _is_configured():
        return None

    summary = _build_summary(run)
    point_id = str(uuid.uuid4())

    try:
        from qdrant_client.models import PointStruct

        from app.embeddings import get_embedding_provider
        from app.qdrant import ensure_collection, get_qdrant_client

        await ensure_collection(_MEMORY_COLLECTION)
        vector = await get_embedding_provider().embed_text(summary)
        await get_qdrant_client().upsert(
            collection_name=_MEMORY_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "summary": summary,
                        "run_id": run.id,
                        "tenant_id": run.tenant_id,
                        "definition_id": run.definition_id,
                    },
                )
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("save_memory: Qdrant upsert failed (%s): %s", type(exc).__name__, exc)
        point_id = None

    mem = AgentMemory(
        tenant_id=run.tenant_id,
        run_id=run.id,
        definition_id=run.definition_id,
        summary=summary,
        qdrant_id=point_id,
    )
    session.add(mem)
    await session.commit()
    logger.info("save_memory: stored memory for run %d (qdrant_id=%s)", run.id, point_id)
    return mem


async def recall_memories(*, query: str, tenant_id: int, top_k: int = 3) -> str | None:
    """Return formatted past memories relevant to `query`, or None when unconfigured.

    The returned string is injected into the agent's system prompt so it has
    context about prior similar runs before it starts reasoning.
    """
    if not _is_configured() or not query.strip():
        return None

    try:
        from app.embeddings import get_embedding_provider
        from app.qdrant import get_qdrant_client

        vector = await get_embedding_provider().embed_text(query)
        result = await get_qdrant_client().query_points(
            collection_name=_MEMORY_COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
            query_filter={"must": [{"key": "tenant_id", "match": {"value": tenant_id}}]},
        )
        hits = [p for p in result.points if (p.payload or {}).get("summary")]
    except Exception as exc:  # noqa: BLE001
        logger.warning("recall_memories: Qdrant query failed (%s): %s", type(exc).__name__, exc)
        return None

    if not hits:
        return None

    lines = ["Relevant past runs (for context — do not repeat, just learn from them):"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"{i}. {hit.payload['summary']}")
    return "\n".join(lines)
