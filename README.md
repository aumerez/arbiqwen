# Arbi

Arbi is an operations assistant platform.

- `backend/` — FastAPI backend (see below)
- `web/` — React/Vite web client

## Backend

FastAPI service exposing the API the web client consumes.

### Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Check it:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```
