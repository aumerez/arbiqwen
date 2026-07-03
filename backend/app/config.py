import re
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Strips userinfo (the part before `@` in a URL authority) before logging
# so a credentialed URL doesn't leak the password to log files.
_URL_USERINFO_RE = re.compile(r"://[^/@\s]+@")


def _redact_url_userinfo(url: str | None) -> str | None:
    if not url:
        return url
    return _URL_USERINFO_RE.sub("://***@", url)


class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = Field("INFO", description="Root log level (DEBUG, INFO, WARNING, ERROR)")

    # Database
    # Postgres is the default for shared dev + prod. SQLite is still supported
    # for one-off scripts — set DATABASE_URL to a sqlite+aiosqlite URL and the
    # connection layer switches dialect-specific behavior (FK pragma, pool
    # class) automatically.
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://arbi:arbi@localhost:5432/arbi",
        description="SQLAlchemy async URL. Defaults to local docker-compose Postgres.",
    )
    DATABASE_ECHO: bool = Field(False, description="Echo all SQL to console (debug only)")
    DATABASE_POOL_SIZE: int = Field(
        10,
        description="Warm connections held in the pool (ignored on SQLite)",
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        10,
        description="Burst connections allowed above pool_size before blocking (ignored on SQLite)",
    )
    DATABASE_POOL_RECYCLE: int = Field(
        1800,
        description="Seconds before a pooled connection is recycled — guards against stale conns behind proxies",
    )

    # JWT — the default is an insecure dev value so the app boots out of the
    # box. Set a strong random 32+ byte JWT_SECRET for any shared or prod
    # deployment.
    JWT_SECRET: str = Field(
        "dev-insecure-secret-change-me-32-bytes-min",
        min_length=32,
        description="HS256 signing key. Override with a strong random value in production.",
    )
    JWT_EXPIRES_IN: str = Field("15m", description="Access token lifetime (e.g. 15m, 2h, 1d)")
    REFRESH_TOKEN_EXPIRES_IN: str = Field("7d", description="Refresh token lifetime")

    # LLM provider
    LLM_PROVIDER: str = Field("anthropic", description="Active LLM provider key")
    ANTHROPIC_API_KEY: str | None = Field(None, description="Anthropic API key (required to make live calls)")
    ANTHROPIC_BASE_URL: str | None = Field(None, description="Override the Anthropic API base URL")
    ANTHROPIC_MODEL: str = Field("claude-sonnet-4-6", description="Default Claude model")

    # Embeddings
    EMBEDDING_PROVIDER: str = Field("openai", description="Active embedding provider key")
    OPENAI_API_KEY: str | None = Field(None, description="OpenAI API key (required for live embedding calls)")
    OPENAI_BASE_URL: str | None = Field(None, description="Override the OpenAI API base URL")
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-3-small", description="OpenAI embedding model (1536-dim)")

    # Reranker (cross-encoder over retrieval results)
    ENABLE_RERANKER: bool = Field(True, description="Enable cross-encoder reranking in the RAG pipeline")
    RERANKER_PROVIDER: str = Field("local", description="Reranker implementation key")
    RERANKER_MODEL: str = Field("BAAI/bge-reranker-large", description="Cross-encoder model for reranking")

    # Storage (document files)
    STORAGE_PROVIDER: str = Field("local", description="File storage backend")
    STORAGE_LOCAL_PATH: str = Field("./uploads", description="Local storage root for uploaded files")

    # Vector store (Qdrant)
    QDRANT_URL: str = Field("http://localhost:6333", description="Qdrant HTTP URL")
    QDRANT_API_KEY: str | None = Field(None, description="Qdrant API key (empty for local instances)")
    QDRANT_COLLECTION: str = Field("documents", description="Default collection name")
    QDRANT_VECTOR_SIZE: int = Field(1536, description="Embedding dimension for the default collection")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars without failing startup
    )


settings = Settings()
