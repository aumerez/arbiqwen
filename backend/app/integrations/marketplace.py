"""Marketplace catalog of installable integrations.

Static, tenant-agnostic metadata. Install state (who has what connected) lives
in the integrations table, not here.
"""

MARKETPLACE_TILES: list[dict] = [
    {
        "key": "slack",
        "name": "Slack",
        "description": "Read channels and post messages in your Slack workspace.",
        "category": "communication",
        "icon_name": "slack",
        "auth_type": "apikey",
        "config_fields": [
            {"key": "bot_token", "label": "Bot Token", "secret": True, "required": True},
        ],
    },
    {
        "key": "github",
        "name": "GitHub",
        "description": "Read issues, pull requests, and repository activity.",
        "category": "development",
        "icon_name": "github",
        "auth_type": "oauth",
        "config_fields": [],
    },
    {
        "key": "google_drive",
        "name": "Google Drive",
        "description": "Import documents from Google Drive into the knowledge base.",
        "category": "storage",
        "icon_name": "hard-drive",
        "auth_type": "oauth",
        "config_fields": [],
    },
    {
        "key": "webhook",
        "name": "Webhook",
        "description": "Send events to an external HTTP endpoint.",
        "category": "automation",
        "icon_name": "webhook",
        "auth_type": "apikey",
        "config_fields": [
            {"key": "url", "label": "Endpoint URL", "secret": False, "required": True},
        ],
    },
]

_BY_KEY = {t["key"]: t for t in MARKETPLACE_TILES}


def list_marketplace_tiles() -> list[dict]:
    return MARKETPLACE_TILES


def get_tile(key: str) -> dict | None:
    return _BY_KEY.get(key)
