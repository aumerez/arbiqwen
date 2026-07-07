"""Minimal async Plane API client (self-hosted, API-key auth).

Wraps the couple of Plane endpoints the agent needs. Auth is a static
`X-API-Key` header; the base URL is scoped to a workspace:

    <PLANE_BASE_URL>/api/v1/workspaces/<slug>/

Kept deliberately small — this is the demo surface (create + list work items),
not a full SDK. Config comes from settings; `PlaneNotConfigured` is raised when
the required env vars are absent so the agent surfaces a clear tool error
instead of making a malformed request.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

# Plane priority enum; anything else is coerced to "none" by the API.
PLANE_PRIORITIES = ("urgent", "high", "medium", "low", "none")

_TIMEOUT = httpx.Timeout(20.0)


class PlaneNotConfigured(RuntimeError):
    """Plane env vars are missing — the tool can't make a live call."""


class PlaneError(RuntimeError):
    """A Plane API call returned a non-2xx response."""


def _base_url() -> str:
    if not settings.plane_configured:
        raise PlaneNotConfigured(
            "Plane is not configured — set PLANE_BASE_URL, PLANE_API_KEY, and PLANE_WORKSPACE_SLUG."
        )
    host = settings.PLANE_BASE_URL.rstrip("/")
    return f"{host}/api/v1/workspaces/{settings.PLANE_WORKSPACE_SLUG}"


def _headers() -> dict[str, str]:
    return {"X-API-Key": settings.PLANE_API_KEY, "Content-Type": "application/json"}


def _resolve_project(project_id: str | None) -> str:
    resolved = project_id or settings.PLANE_PROJECT_ID
    if not resolved:
        raise PlaneNotConfigured("No Plane project — pass project_id or set PLANE_PROJECT_ID.")
    return resolved


async def create_task(
    *,
    name: str,
    description_html: str | None = None,
    priority: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Create a Plane work item (issue). Returns the created item JSON."""
    base = _base_url()
    project = _resolve_project(project_id)
    payload: dict[str, Any] = {"name": name}
    if description_html:
        payload["description_html"] = description_html
    if priority:
        payload["priority"] = priority if priority in PLANE_PRIORITIES else "none"

    url = f"{base}/projects/{project}/issues/"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=_headers())
    if resp.status_code >= 400:
        raise PlaneError(f"Plane create_task failed ({resp.status_code}): {resp.text[:500]}")
    return resp.json()


async def list_tasks(*, project_id: str | None = None) -> list[dict[str, Any]]:
    """List work items in a project. Returns the results list."""
    base = _base_url()
    project = _resolve_project(project_id)
    url = f"{base}/projects/{project}/issues/"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_headers())
    if resp.status_code >= 400:
        raise PlaneError(f"Plane list_tasks failed ({resp.status_code}): {resp.text[:500]}")
    body = resp.json()
    # Plane paginates list responses under "results"; tolerate a bare list too.
    return body.get("results", body) if isinstance(body, dict) else body
