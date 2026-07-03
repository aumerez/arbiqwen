"""Qdrant client connection.

A single lazily-built `AsyncQdrantClient` shared across the process. The client
is created on first use so importing this module never opens a socket — the app
boots even when Qdrant is unreachable.
"""

from app.config import settings

_client = None


def get_qdrant_client():
    global _client
    if _client is None:
        from qdrant_client import AsyncQdrantClient

        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
    return _client
