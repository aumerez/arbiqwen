"""Tests for GET /artifacts/{id}/content — streams the raw artifact body with
its content type for the web preview panel."""

import pytest

from app.chat.models import Chat
from app.dashboards.models import Artifact


async def _artifact(db, tmp_path, *, tenant_id=1, content_type="text/html", body=b"<h1>Dashboard</h1>", on_disk=True):
    chat = Chat(tenant_id=tenant_id, user_id=1, title="c")
    db.add(chat)
    await db.flush()
    path = tmp_path / "artifact.html"
    if on_disk:
        path.write_bytes(body)
    artifact = Artifact(
        tenant_id=tenant_id,
        chat_id=chat.id,
        skill_key="chart",
        filename="artifact.html",
        content_type=content_type,
        title="Preview",
        storage_path=str(path),
        size_bytes=len(body),
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


@pytest.mark.asyncio
async def test_get_content_returns_body_and_type(client, db, auth_headers, tmp_path):
    artifact = await _artifact(db, tmp_path, body=b"<h1>Hi</h1>", content_type="text/html")
    resp = await client.get(f"/artifacts/{artifact.id}/content", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.text == "<h1>Hi</h1>"
    assert resp.headers["content-type"].startswith("text/html")


@pytest.mark.asyncio
async def test_get_content_markdown_type_preserved(client, db, auth_headers, tmp_path):
    artifact = await _artifact(db, tmp_path, body=b"# Title", content_type="text/markdown")
    resp = await client.get(f"/artifacts/{artifact.id}/content", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.text == "# Title"
    assert resp.headers["content-type"].startswith("text/markdown")


@pytest.mark.asyncio
async def test_get_content_unknown_id_404(client, auth_headers):
    assert (await client.get("/artifacts/9999/content", headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_get_content_missing_file_404(client, db, auth_headers, tmp_path):
    artifact = await _artifact(db, tmp_path, on_disk=False)
    resp = await client.get(f"/artifacts/{artifact.id}/content", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_content_requires_auth(client, db, tmp_path):
    artifact = await _artifact(db, tmp_path)
    assert (await client.get(f"/artifacts/{artifact.id}/content")).status_code == 401


@pytest.mark.asyncio
async def test_get_content_scoped_to_tenant(client, db, auth_headers, tmp_path):
    # Artifact belongs to a different tenant → 404 for this caller.
    artifact = await _artifact(db, tmp_path, tenant_id=999)
    resp = await client.get(f"/artifacts/{artifact.id}/content", headers=auth_headers)
    assert resp.status_code == 404
