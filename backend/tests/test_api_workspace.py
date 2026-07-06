"""API tests for the workspace surfaces: projects, agents, skills, playbooks, dashboards."""


async def _project(client, auth_headers, name="WS"):
    return (await client.post("/projects", headers=auth_headers, json={"name": name})).json()


# --- projects ---
async def test_projects_crud(client, auth_headers):
    p = await _project(client, auth_headers)
    assert (await client.get("/projects", headers=auth_headers)).json()[0]["id"] == p["id"]
    r = await client.patch(f"/projects/{p['id']}", headers=auth_headers, json={"name": "Renamed"})
    assert r.json()["name"] == "Renamed"
    assert (await client.delete(f"/projects/{p['id']}", headers=auth_headers)).status_code == 204


async def test_project_missing_404(client, auth_headers):
    assert (await client.get("/projects/999", headers=auth_headers)).status_code == 404


# --- agents ---
async def test_agents_crud(client, auth_headers):
    r = await client.post(
        "/api/agents",
        headers=auth_headers,
        json={"title": "Summarizer", "prompt_template": "Summarize {x}", "steps": ["a"], "allowed_tools": []},
    )
    assert r.status_code == 201
    agent_id = r.json()["id"]
    assert (await client.get("/api/agents", headers=auth_headers)).json()[0]["title"] == "Summarizer"
    patched = await client.patch(f"/api/agents/{agent_id}", headers=auth_headers, json={"status": "queued"})
    assert patched.json()["status"] == "queued"
    assert (await client.delete(f"/api/agents/{agent_id}", headers=auth_headers)).status_code == 204


# --- skills ---
async def test_skills_list_and_toggle(client, auth_headers):
    skills = (await client.get("/skills", headers=auth_headers)).json()
    assert len(skills) == 4
    assert all(s["enabled"] for s in skills)
    off = await client.put("/skills/web_search/toggle", headers=auth_headers, json={"enabled": False})
    assert off.json()["enabled"] is False
    after = {s["key"]: s["enabled"] for s in (await client.get("/skills", headers=auth_headers)).json()}
    assert after["web_search"] is False


async def test_skills_unknown_404(client, auth_headers):
    r = await client.put("/skills/nope/toggle", headers=auth_headers, json={"enabled": True})
    assert r.status_code == 404


# --- playbooks ---
async def test_playbooks_crud_and_run(client, auth_headers):
    p = await _project(client, auth_headers)
    created = await client.post(
        "/playbooks",
        headers=auth_headers,
        json={"project_id": p["id"], "name": "Onboarding", "steps": [{"id": "s1", "order": 1, "type": "action", "name": "n"}]},
    )
    assert created.status_code == 201
    pb_id = created.json()["id"]
    run = await client.post(f"/playbooks/{pb_id}/run", headers=auth_headers)
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["steps_total"] == 1


# --- dashboards + artifacts ---
async def test_dashboards_and_from_artifact(client, auth_headers, db):
    from app.chat.models import Chat
    from app.dashboards.models import Artifact

    p = await _project(client, auth_headers)

    chat = Chat(tenant_id=1, user_id=1, title="c")
    db.add(chat)
    await db.flush()
    artifact = Artifact(
        tenant_id=1, chat_id=chat.id, skill_key="chart", filename="c.html",
        content_type="text/html", title="Sales Chart", storage_path="/tmp/c.html", size_bytes=10,
    )
    db.add(artifact)
    await db.commit()

    made = await client.post(
        "/dashboards", headers=auth_headers,
        json={"project_id": p["id"], "title": "Overview", "spec": {"type": "chart"}, "skill_name": "chart"},
    )
    assert made.status_code == 201

    promoted = await client.post(
        f"/dashboards/from-artifact/{artifact.id}", headers=auth_headers, json={"project_id": p["id"]}
    )
    assert promoted.status_code == 201
    assert promoted.json()["title"] == "Sales Chart"

    assert len((await client.get("/dashboards", headers=auth_headers)).json()) == 2
    assert len((await client.get("/artifacts", headers=auth_headers)).json()) == 1
