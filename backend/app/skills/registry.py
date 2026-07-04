"""Built-in skill registry.

Skills are the capabilities the assistant can call during a chat turn. The
registry is static metadata; per-workspace enablement and config live in the
tenant_skill_configs table.
"""

BUILTIN_SKILLS: list[dict] = [
    {
        "key": "document_search",
        "name": "Document Search",
        "description": "Search the knowledge base for relevant document passages.",
        "category": "retrieval",
        "icon_name": "search",
        "version": "1.0",
    },
    {
        "key": "table_query",
        "name": "Table Query",
        "description": "Answer precise questions over an uploaded spreadsheet or CSV.",
        "category": "data",
        "icon_name": "table",
        "version": "1.0",
    },
    {
        "key": "chart",
        "name": "Chart Builder",
        "description": "Render a chart from a set of data points.",
        "category": "visualization",
        "icon_name": "bar-chart",
        "version": "1.0",
    },
    {
        "key": "web_search",
        "name": "Web Search",
        "description": "Look up current information on the public web.",
        "category": "retrieval",
        "icon_name": "globe",
        "version": "1.0",
    },
]

_BY_KEY = {s["key"]: s for s in BUILTIN_SKILLS}


def get_skill(key: str) -> dict | None:
    return _BY_KEY.get(key)
