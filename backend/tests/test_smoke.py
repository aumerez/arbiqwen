"""Smoke tests — the app boots and every router is wired and reachable."""

import pytest


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_all_tables_created(engine):
    """Every model's table exists in the schema built by create_all."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        rows = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {r[0] for r in rows}
    expected = {
        "users",
        "refresh_tokens",
        "documents",
        "document_chunks",
        "tenant_rag_sources",
        "chats",
        "chat_messages",
        "projects",
        "agent_definitions",
        "agent_runs",
        "tenant_skill_configs",
        "playbooks",
        "playbook_runs",
        "artifacts",
        "dashboards",
        "integrations",
        "integration_connections",
        "oauth_tokens",
    }
    assert expected.issubset(tables)


# One authenticated GET per router — proves the router is mounted and the auth
# dependency is enforced (401 without a token, 2xx with one).
AUTHED_GETS = [
    "/chats",
    "/documents/",
    "/projects",
    "/agent/definitions",
    "/skills",
    "/playbooks",
    "/dashboards",
    "/artifacts",
    "/api/rag-sources",
    "/api/rag-sources/drivers",
    "/api/integrations/",
    "/api/integrations/marketplace",
    "/integrations-config",
]


@pytest.mark.parametrize("path", AUTHED_GETS)
async def test_router_requires_auth(client, path):
    r = await client.get(path)
    assert r.status_code == 401


@pytest.mark.parametrize("path", AUTHED_GETS)
async def test_router_reachable_with_auth(client, auth_headers, path):
    r = await client.get(path, headers=auth_headers)
    assert r.status_code == 200
