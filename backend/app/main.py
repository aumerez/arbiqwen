from app.shared.logging import setup_logging

setup_logging()

from fastapi import FastAPI

from app.shared.errors import register_exception_handlers

app = FastAPI(title="Arbi Backend")

register_exception_handlers(app)


@app.get("/health")
async def health():
    """Liveness probe for container orchestration."""
    return {"status": "ok"}
