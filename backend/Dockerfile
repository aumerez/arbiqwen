# syntax=docker/dockerfile:1
# Builder stage — install dependencies into system Python.
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy dependency manifest and install into the system interpreter.
COPY pyproject.toml ./
RUN uv pip install --system .

# Final stage
FROM python:3.12-slim

WORKDIR /app

# curl for the container healthcheck.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Non-root runtime user.
RUN adduser --disabled-password --gecos "" appuser

# Copy installed packages from the builder.
COPY --from=builder /usr/local /usr/local

# Application code.
COPY . .

# Pre-create the uploads dir owned by appuser so a fresh named volume mounts
# writable for the non-root process.
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
