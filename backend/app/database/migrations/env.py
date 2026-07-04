import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.database.base import Base

# Import model modules so their tables register on Base.metadata for autogenerate.
import app.auth.models  # noqa: F401
import app.documents.models  # noqa: F401
import app.rag_sources.models  # noqa: F401
import app.chat.models  # noqa: F401
import app.projects.models  # noqa: F401
import app.agents.models  # noqa: F401
import app.skills.models  # noqa: F401
import app.playbooks.models  # noqa: F401
import app.dashboards.models  # noqa: F401
import app.integrations.models  # noqa: F401

# Load .env file so DATABASE_URL is available without setting system env vars
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    return os.getenv("DATABASE_URL")


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # SQLite needs batch mode for ALTER TABLE
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    configuration = config.get_main_option("sqlalchemy.url")
    if configuration is None:
        configuration = get_url()
    connectable = async_engine_from_config(
        {"sqlalchemy.url": configuration},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
