"""RAG retrieval: embed the query, search the vector store, rerank the hits."""

import logging
from dataclasses import dataclass

from app.config import settings
from app.embeddings import get_embedding_provider
from app.qdrant import get_qdrant_client
from app.reranker import get_reranker

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    document_id: int | None
    chunk_index: int | None


def _embedding_configured() -> bool:
    if settings.EMBEDDING_PROVIDER == "dashscope":
        return bool(settings.DASHSCOPE_API_KEY)
    return bool(settings.OPENAI_API_KEY)


async def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Return the most relevant chunks for a query.

    Guarded: with no embedding key or an empty/unreachable index, returns an
    empty list so the chat still answers (without grounded context) instead of
    erroring.
    """
    if not _embedding_configured():
        return []

    try:
        query_vector = await get_embedding_provider().embed_text(query)
        # Over-fetch, then let the reranker narrow to the best top_k.
        result = await get_qdrant_client().query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            limit=top_k * 3,
            with_payload=True,
        )
        hits = [
            RetrievedChunk(
                text=(p.payload or {}).get("text", ""),
                score=p.score,
                document_id=(p.payload or {}).get("document_id"),
                chunk_index=(p.payload or {}).get("chunk_index"),
            )
            for p in result.points
        ]
    except Exception as exc:  # noqa: BLE001 — retrieval degrades to no-context, never 500s
        logger.warning("Retrieval failed (%s): %s", type(exc).__name__, exc)
        return []

    hits = [h for h in hits if h.text]
    if not hits:
        return []

    reranked = await get_reranker().rerank(query, [h.text for h in hits], top_k=top_k)
    by_text = {h.text: h for h in hits}
    return [by_text[t] for t in reranked if t in by_text]
