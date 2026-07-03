"""Vector indexing for document chunks.

Embeds chunk text and upserts it into the Qdrant collection so the chat
retrieval pipeline can find it. Guarded end to end: if embeddings aren't
configured or Qdrant is unreachable, indexing is skipped with a warning rather
than failing the upload.
"""

import logging

from app.config import settings
from app.embeddings import get_embedding_provider
from app.qdrant import ensure_collection, get_qdrant_client

logger = logging.getLogger(__name__)


def _point_id(document_id: int, chunk_index: int) -> int:
    # Deterministic, collision-free id per (document, chunk) so re-indexing a
    # document overwrites its points instead of duplicating them.
    return document_id * 1_000_000 + chunk_index


async def index_document(document_id: int, chunks: list[str]) -> int:
    """Embed and upsert a document's chunks. Returns the number indexed (0 if skipped)."""
    if not chunks:
        return 0
    if not settings.OPENAI_API_KEY:
        logger.info("Vector indexing skipped for document %s: no embedding key configured", document_id)
        return 0

    try:
        from qdrant_client.models import PointStruct

        vectors = await get_embedding_provider().embed_batch(chunks)
        await ensure_collection()
        points = [
            PointStruct(
                id=_point_id(document_id, i),
                vector=vector,
                payload={"document_id": document_id, "chunk_index": i, "text": text},
            )
            for i, (text, vector) in enumerate(zip(chunks, vectors))
        ]
        await get_qdrant_client().upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
        return len(points)
    except Exception as exc:  # noqa: BLE001 — indexing is best-effort, never blocks upload
        logger.warning("Vector indexing failed for document %s (%s): %s", document_id, type(exc).__name__, exc)
        return 0
