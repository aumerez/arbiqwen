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

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars without failing startup
    )


settings = Settings()
