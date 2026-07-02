from fastapi import FastAPI

app = FastAPI(title="Arbi Backend")


@app.get("/health")
async def health():
    """Liveness probe for container orchestration."""
    return {"status": "ok"}
