"""Tests for the approve/reject endpoints of the human-in-the-loop checkpoint."""

import pytest

from app.agents import routes as routes_mod
from app.agents.models import AgentDefinition, AgentRun, AgentStatus


@pytest.fixture
def fake_plane(monkeypatch):
    """Stub the Plane write so approve can execute the pending action offline."""
    calls: list[dict] = []

    async def fake_create(**kwargs):
        calls.append(kwargs)
        return {"id": "u1", "sequence_id": 9, "name": kwargs["name"], "priority": kwargs.get("priority")}

    monkeypatch.setattr("app.integrations.plane_client.create_task", fake_create)
    return calls


@pytest.fixture
def no_execute(monkeypatch):
    scheduled: list[int] = []
    monkeypatch.setattr(routes_mod, "run_agent", lambda run_id: scheduled.append(run_id))
    return scheduled


async def _waiting_run(db, *, user_id=1, args=None):
    definition = AgentDefinition(
        name="Lead Intake",
        prompt_template="handle it",
        allowed_tools=["plane_create_task"],
        user_id=user_id,
        tenant_id=1,
    )
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    run = AgentRun(
        definition_id=definition.id,
        user_id=user_id,
        tenant_id=1,
        status=AgentStatus.waiting_approval.value,
        pending_action={
            "calls": [
                {
                    "id": "c1",
                    "name": "plane_create_task",
                    "arguments": args or {"name": "Call Acme", "priority": "high"},
                    "requires_approval": True,
                }
            ]
        },
        messages=[
            {"role": "user", "content": "handle it"},
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "c1", "name": "plane_create_task", "input": args or {}}],
            },
        ],
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@pytest.mark.asyncio
async def test_approve_executes_and_resumes(client, db, auth_headers, fake_plane, no_execute):
    run = await _waiting_run(db)
    resp = await client.post(f"/agent/runs/{run.id}/approve", headers=auth_headers, json={})
    assert resp.status_code == 202
    assert resp.json()["status"] == AgentStatus.working.value
    # Pending write executed against (faked) Plane, loop rescheduled.
    assert fake_plane[0]["name"] == "Call Acme"
    assert no_execute == [run.id]

    await db.refresh(run)
    assert run.pending_action is None
    # tool_result appended to the saved conversation for the resume.
    assert run.messages[-1]["role"] == "user"


@pytest.mark.asyncio
async def test_approve_with_edited_input(client, db, auth_headers, fake_plane, no_execute):
    run = await _waiting_run(db)
    resp = await client.post(
        f"/agent/runs/{run.id}/approve",
        headers=auth_headers,
        json={"edited_input": {"name": "Call Acme Corp", "priority": "urgent"}},
    )
    assert resp.status_code == 202
    assert fake_plane[0]["name"] == "Call Acme Corp"
    assert fake_plane[0]["priority"] == "urgent"


@pytest.mark.asyncio
async def test_approve_conflict_when_not_waiting(client, db, auth_headers, fake_plane, no_execute):
    run = await _waiting_run(db)
    run.status = AgentStatus.working.value
    await db.commit()
    resp = await client.post(f"/agent/runs/{run.id}/approve", headers=auth_headers, json={})
    assert resp.status_code == 409
    assert fake_plane == []


@pytest.mark.asyncio
async def test_reject_terminates_without_executing(client, db, auth_headers, fake_plane, no_execute):
    run = await _waiting_run(db)
    resp = await client.post(f"/agent/runs/{run.id}/reject", headers=auth_headers, json={"reason": "not a real lead"})
    assert resp.status_code == 200
    assert resp.json()["status"] == AgentStatus.rejected.value
    assert "rejected" in resp.json()["result_md"].lower()
    # No write, no resume.
    assert fake_plane == []
    assert no_execute == []

    await db.refresh(run)
    assert run.completed_at is not None


@pytest.mark.asyncio
async def test_reject_conflict_when_not_waiting(client, db, auth_headers, no_execute):
    run = await _waiting_run(db)
    run.status = AgentStatus.done.value
    await db.commit()
    assert (await client.post(f"/agent/runs/{run.id}/reject", headers=auth_headers, json={})).status_code == 409


@pytest.mark.asyncio
async def test_approve_scoped_to_owner(client, db, auth_headers, fake_plane, no_execute):
    run = await _waiting_run(db, user_id=999)
    resp = await client.post(f"/agent/runs/{run.id}/approve", headers=auth_headers, json={})
    assert resp.status_code == 404
    assert fake_plane == []
