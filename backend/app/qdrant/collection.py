"""Qdrant collection management and guarded startup initialization."""

import logging

from app.config import settings
from app.qdrant.connection import get_qdrant_client

logger = logging.getLogger(__name__)


async def ensure_collection(name: str | None = None, vector_size: int | None = None) -> None:
    """Create the collection if it does not already exist (idempotent)."""
    from qdrant_client.models import Distance, VectorParams

    client = get_qdrant_client()
    name = name or settings.QDRANT_COLLECTION
    vector_size = vector_size or settings.QDRANT_VECTOR_SIZE

    existing = {c.name for c in (await client.get_collections()).collections}
    if name in existing:
        return

    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logger.info("Created Qdrant collection %s (size=%d)", name, vector_size)


async def init_qdrant() -> None:
    """Startup hook: ensure the default collection exists.

    Guarded — a missing or unreachable Qdrant must not stop the app from
    booting. The failure is logged and the RAG features degrade rather than
    taking the whole service down.
    """
    try:
        await ensure_collection()
    except Exception as exc:  # noqa: BLE001 — startup must never hard-fail here
        logger.warning("Qdrant init skipped (%s): %s", type(exc).__name__, exc)
