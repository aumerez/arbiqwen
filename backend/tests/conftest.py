"""Shared test fixtures.

Every test runs against an in-memory SQLite database (StaticPool so a single
connection is shared, keeping the schema alive for the session). The FastAPI
`get_session` dependency is overridden to use that database, so API tests hit
the real routers without a live Postgres/Qdrant/LLM.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Import every model module so Base.metadata knows all tables for create_all.
import app.agents.models  # noqa: F401,E402
import app.chat.models  # noqa: F401,E402
import app.dashboards.models  # noqa: F401,E402
import app.documents.models  # noqa: F401,E402
import app.integrations.models  # noqa: F401,E402
import app.integrations.oauth_models  # noqa: F401,E402
import app.playbooks.models  # noqa: F401,E402
import app.projects.models  # noqa: F401,E402
import app.rag_sources.models  # noqa: F401,E402
import app.skills.models  # noqa: F401,E402
from app.auth.jwt import create_access_token
from app.auth.models import User
from app.auth.password import hash_password
from app.database.base import Base
from app.database.connection import get_session
from app.main import app as fastapi_app
from app.shared.rate_limit import limiter

# Rate limiting is infrastructure, not per-test behavior — disable it so tests
# don't flake on shared cross-test request counts.
limiter.enabled = False


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(session_factory):
    """A session for arranging test data directly."""
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def client(session_factory):
    """An HTTP client whose requests use the test database."""

    async def _override_get_session():
        # Mirror the real get_session: commit after the request unless it errored.
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    fastapi_app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(db):
    """A persisted user (id=1, role admin)."""
    u = User(email="tester@arbi.dev", password_hash=hash_password("secret123"), role="admin")
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
def auth_headers(user):
    """Bearer headers for the seeded user (token decoded by get_current_user, no DB lookup)."""
    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "tenant_id": user.tenant_id, "role": user.role}
    )
    return {"Authorization": f"Bearer {token}"}
