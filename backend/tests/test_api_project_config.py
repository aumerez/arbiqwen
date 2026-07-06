"""API tests for per-project RAG-source and integration config."""


async def _project(client, auth_headers):
    return (await client.post("/projects", headers=auth_headers, json={"name": "WS"})).json()["id"]


async def _rag_source(client, auth_headers):
    return (
        await client.post("/api/rag-sources", headers=auth_headers, json={"rag_key": "qdrant", "label": "KB"})
    ).json()["id"]


async def _integration(client, auth_headers):
    return (
        await client.post("/api/integrations/slack/connect", headers=auth_headers, json={"alias": "S", "config": {}})
    ).json()["id"]


async def test_project_rag_sources_enable_list_disable(client, auth_headers):
    pid = await _project(client, auth_headers)
    sid = await _rag_source(client, auth_headers)

    assert (await client.get(f"/projects/{pid}/rag-sources", headers=auth_headers)).json() == []

    enabled = await client.post(f"/projects/{pid}/rag-sources/{sid}", headers=auth_headers)
    assert enabled.status_code == 201
    assert enabled.json()["status"] == "enabled"

    # Idempotent.
    again = await client.post(f"/projects/{pid}/rag-sources/{sid}", headers=auth_headers)
    assert again.json()["status"] == "already_enabled"

    assert (await client.get(f"/projects/{pid}/rag-sources", headers=auth_headers)).json() == [sid]

    assert (await client.delete(f"/projects/{pid}/rag-sources/{sid}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/projects/{pid}/rag-sources", headers=auth_headers)).json() == []


async def test_project_integrations_config(client, auth_headers):
    pid = await _project(client, auth_headers)
    iid = await _integration(client, auth_headers)

    empty = await client.get(f"/projects/{pid}/integrations-config", headers=auth_headers)
    assert empty.json() == {"integration_ids": [], "integration_keys": []}

    assert (await client.post(f"/projects/{pid}/integrations-config/{iid}", headers=auth_headers)).status_code == 201
    body = (await client.get(f"/projects/{pid}/integrations-config", headers=auth_headers)).json()
    assert body["integration_ids"] == [iid]

    assert (await client.delete(f"/projects/{pid}/integrations-config/{iid}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/projects/{pid}/integrations-config", headers=auth_headers)).json()["integration_ids"] == []


async def test_project_oauth_integrations_config(client, auth_headers):
    pid = await _project(client, auth_headers)

    assert (await client.post(f"/projects/{pid}/oauth-integrations-config/google-drive", headers=auth_headers)).status_code == 201
    body = (await client.get(f"/projects/{pid}/integrations-config", headers=auth_headers)).json()
    assert body["integration_keys"] == ["google-drive"]

    assert (await client.delete(f"/projects/{pid}/oauth-integrations-config/google-drive", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/projects/{pid}/integrations-config", headers=auth_headers)).json()["integration_keys"] == []


async def test_project_config_requires_auth(client):
    assert (await client.get("/projects/1/rag-sources")).status_code == 401


async def test_project_config_missing_project_404(client, auth_headers):
    assert (await client.get("/projects/999/rag-sources", headers=auth_headers)).status_code == 404
