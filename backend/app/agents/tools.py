"""Agent tool registry — maps tool names to callables + their schemas.

The loop asks for a registry filtered by a definition's `allowed_tools`; only
whitelisted tools are exposed to the model and executable. Each callable takes
the parsed arguments dict and returns a JSON-serializable result (a dict with an
`error` key marks a failed call, which the dispatcher surfaces to the model as
an error tool_result).

This PR wires Plane (create/list work items). Twenty CRM tools land in a
follow-up PR and register here the same way.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.agents._runtime import ToolRegistry
from app.integrations import plane_client
from app.integrations.plane_client import PlaneError, PlaneNotConfigured

logger = logging.getLogger(__name__)

ToolFn = Callable[[dict], Awaitable[Any]]


# --- Plane tools ----------------------------------------------------------


async def _plane_create_task(args: dict) -> dict:
    name = (args.get("name") or "").strip()
    if not name:
        return {"error": "name is required"}
    try:
        item = await plane_client.create_task(
            name=name,
            description_html=args.get("description_html"),
            priority=args.get("priority"),
            project_id=args.get("project_id"),
        )
        return {
            "id": item.get("id"),
            "sequence_id": item.get("sequence_id"),
            "name": item.get("name", name),
            "priority": item.get("priority"),
        }
    except (PlaneNotConfigured, PlaneError) as exc:
        return {"error": str(exc)}


async def _plane_list_tasks(args: dict) -> dict:
    try:
        items = await plane_client.list_tasks(project_id=args.get("project_id"))
        return {
            "count": len(items),
            "tasks": [
                {"id": i.get("id"), "sequence_id": i.get("sequence_id"), "name": i.get("name")} for i in items[:50]
            ],
        }
    except (PlaneNotConfigured, PlaneError) as exc:
        return {"error": str(exc)}


# name -> (callable, Anthropic-native tool schema)
_TOOLS: dict[str, tuple[ToolFn, dict]] = {
    "plane_create_task": (
        _plane_create_task,
        {
            "name": "plane_create_task",
            "description": "Create a task (work item) in Plane. Use for follow-ups and action items.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task title."},
                    "description_html": {"type": "string", "description": "Optional HTML description."},
                    "priority": {
                        "type": "string",
                        "enum": ["urgent", "high", "medium", "low", "none"],
                        "description": "Optional priority.",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Optional project UUID; defaults to configured project.",
                    },
                },
                "required": ["name"],
            },
        },
    ),
    "plane_list_tasks": (
        _plane_list_tasks,
        {
            "name": "plane_list_tasks",
            "description": "List existing tasks (work items) in a Plane project.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Optional project UUID; defaults to configured project.",
                    },
                },
            },
        },
    ),
}


# Tools that mutate external systems — these pause the run at a human-in-the-loop
# checkpoint before executing. Read-only tools run without approval.
_APPROVAL_REQUIRED = {"plane_create_task"}


def requires_approval(tool_name: str) -> bool:
    """Whether calling this tool must pause for human approval first."""
    return tool_name in _APPROVAL_REQUIRED


def build_registry(allowed_tools: list[str]) -> tuple[ToolRegistry, list[dict]]:
    """Return (registry, tool_definitions) for the whitelisted tools.

    Unknown names in `allowed_tools` are ignored (logged) — a definition may
    reference a tool that isn't implemented yet.
    """
    registry: ToolRegistry = {}
    definitions: list[dict] = []
    for name in allowed_tools or []:
        entry = _TOOLS.get(name)
        if entry is None:
            logger.info("build_registry: unknown tool %r ignored", name)
            continue
        fn, schema = entry
        registry[name] = fn
        definitions.append(schema)
    return registry, definitions
