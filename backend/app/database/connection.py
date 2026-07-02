from sqlalchemy import event
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

from .base import Base


def _is_sqlite_url(url: str) -> bool:
    return make_url(url).get_backend_name() == "sqlite"


def _build_engine():
    """Create the async engine, switching pool + driver-specific options by dialect.

    Postgres (default): SQLAlchemy's default `AsyncAdaptedQueuePool` with bounded
    pool_size/max_overflow/pool_recycle from settings. Each session gets its own
    connection.

    SQLite (one-off scripts): keep `StaticPool` + `check_same_thread=False` and a
    `connect` listener that fires `PRAGMA foreign_keys = ON` so ON DELETE CASCADE
    actually fires. Postgres enforces FKs unconditionally, so the listener isn't
    installed there.
    """
    sqlite = _is_sqlite_url(settings.DATABASE_URL)

    if sqlite:
        from sqlalchemy.pool import StaticPool

        eng = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        # SQLite does NOT enforce foreign keys by default. Without this PRAGMA,
        # ON DELETE CASCADE is a no-op at the DB level. Postgres enforces FKs
        # unconditionally, so this listener is only attached on the SQLite path.
        @event.listens_for(eng.sync_engine, "connect")
        def _enable_fk_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

        return eng

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
    )


engine = _build_engine()

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncSession:
    """Dependency provider for FastAPI routes that need DB access."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables if not exists) — typically use Alembic instead."""
    async with engine.begin() as conn:
        # In production, use Alembic migrations, not this.
        await conn.run_sync(Base.metadata.create_all)
