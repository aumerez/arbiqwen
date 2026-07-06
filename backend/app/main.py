from app.shared.logging import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.agents.routes import router as agents_router
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.config import settings
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
from app.shared.errors import register_exception_handlers
from app.shared.rate_limit import limiter
from app.skills.routes import router as skills_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Refuse to run in production on the insecure default signing key.
    if settings.is_production and settings.jwt_secret_is_default:
        raise RuntimeError("JWT_SECRET must be set to a strong value in production (the dev default is not allowed).")
    # Guarded — degrades rather than failing boot if Qdrant is unreachable.
    await init_qdrant()
    yield


app = FastAPI(title="Arbi Backend", lifespan=lifespan)

# Rate limiting (slowapi) — protects auth endpoints from brute force.
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(_request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=429, content={"error": {"code": "rate_limited", "message": "Too many requests"}})


# Install CORS only when origins are configured. The browser web client runs on
# a separate origin and cannot call the API without this. Bearer-header auth
# means no cookies, so credentials stay off.
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
