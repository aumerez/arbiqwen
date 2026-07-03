from app.shared.logging import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.qdrant import init_qdrant
from app.shared.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Guarded — degrades rather than failing boot if Qdrant is unreachable.
    await init_qdrant()
    yield


app = FastAPI(title="Arbi Backend", lifespan=lifespan)

register_exception_handlers(app)
app.include_router(auth_router)


@app.get("/health")
async def health():
    """Liveness probe for container orchestration."""
    return {"status": "ok"}
