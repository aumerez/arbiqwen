"""Tests for the agent runs API (instantiate from a definition + history)."""

import pytest

from app.agents import routes as routes_mod
from app.agents.models import AgentStatus


@pytest.fixture
def no_execute(monkeypatch):
    """Capture scheduled runs instead of executing the real loop."""
    scheduled: list[int] = []
    monkeypatch.setattr(routes_mod, "run_agent", lambda run_id: scheduled.append(run_id))
    return scheduled


async def _make_definition(client, auth_headers, name="Lead Intake"):
    r = await client.post(
        "/agent/definitions",
        headers=auth_headers,
        json={"name": name, "prompt_template": "Handle {input}", "allowed_tools": []},
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_run_instantiates_and_schedules(client, auth_headers, no_execute):
    definition_id = await _make_definition(client, auth_headers)

    r = await client.post(
        "/agent/runs",
        headers=auth_headers,
        json={"definition_id": definition_id, "trigger_input": "Jane @ Acme wants a demo"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == AgentStatus.queued.value
    assert body["definition_id"] == definition_id
    assert body["trigger_input"] == "Jane @ Acme wants a demo"
    assert no_execute == [body["id"]]


@pytest.mark.asyncio
async def test_create_run_unknown_definition_404(client, auth_headers, no_execute):
    r = await client.post("/agent/runs", headers=auth_headers, json={"definition_id": 9999})
    assert r.status_code == 404
    assert no_execute == []


@pytest.mark.asyncio
async def test_list_runs_filters_by_definition(client, auth_headers, no_execute):
    def_a = await _make_definition(client, auth_headers, name="A")
    def_b = await _make_definition(client, auth_headers, name="B")
    await client.post("/agent/runs", headers=auth_headers, json={"definition_id": def_a})
    await client.post("/agent/runs", headers=auth_headers, json={"definition_id": def_a})
    await client.post("/agent/runs", headers=auth_headers, json={"definition_id": def_b})

    all_runs = (await client.get("/agent/runs", headers=auth_headers)).json()
    assert len(all_runs) == 3
    only_a = (await client.get(f"/agent/runs?definition_id={def_a}", headers=auth_headers)).json()
    assert len(only_a) == 2
    assert all(run["definition_id"] == def_a for run in only_a)


@pytest.mark.asyncio
async def test_get_run(client, auth_headers, no_execute):
    definition_id = await _make_definition(client, auth_headers)
    created = (await client.post("/agent/runs", headers=auth_headers, json={"definition_id": definition_id})).json()

    got = await client.get(f"/agent/runs/{created['id']}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]

    assert (await client.get("/agent/runs/9999", headers=auth_headers)).status_code == 404
