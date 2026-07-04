from app.shared.logging import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.routes import router as agents_router
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.dashboards.routes import artifacts_router
from app.dashboards.routes import router as dashboards_router
from app.documents.routes import router as documents_router
from app.integrations.oauth_routes import oauth_router as integrations_oauth_router
from app.integrations.routes import config_router as integrations_config_router
from app.integrations.routes import router as integrations_router
from app.playbooks.routes import router as playbooks_router
from app.projects.routes import router as projects_router
from app.qdrant import init_qdrant
from app.rag_sources.routes import router as rag_sources_router
from app.skills.routes import router as skills_router
from app.shared.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Guarded — degrades rather than failing boot if Qdrant is unreachable.
    await init_qdrant()
    yield


app = FastAPI(title="Arbi Backend", lifespan=lifespan)

register_exception_handlers(app)
app.include_router(agents_router)
app.include_router(artifacts_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dashboards_router)
app.include_router(documents_router)
app.include_router(integrations_router)
app.include_router(integrations_oauth_router)
app.include_router(integrations_config_router)
app.include_router(playbooks_router)
app.include_router(projects_router)
app.include_router(rag_sources_router)
app.include_router(skills_router)


@app.get("/health")
async def health():
    """Liveness probe for container orchestration."""
    return {"status": "ok"}
