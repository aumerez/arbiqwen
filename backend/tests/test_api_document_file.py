"""Tests for GET /documents/{id}/file — streams the stored source document for
the web citation/preview panel."""

import pytest

from app.config import settings
from app.documents.models import Document, DocumentStatus
from app.documents.storage import get_storage_provider


async def _document(db, tmp_path, monkeypatch, *, user_id=1, mimetype="text/plain", body=b"hello world", on_disk=True):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    doc = Document(
        tenant_id=1,
        user_id=user_id,
        filename="note.txt",
        mimetype=mimetype,
        size=len(body),
        status=DocumentStatus.indexed,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    if on_disk:
        await get_storage_provider().save_file(doc.tenant_id, doc.id, body, doc.filename)
    return doc


@pytest.mark.asyncio
async def test_get_file_streams_body_and_type(client, db, auth_headers, tmp_path, monkeypatch):
    doc = await _document(db, tmp_path, monkeypatch, body=b"hello world", mimetype="text/plain")
    resp = await client.get(f"/documents/{doc.id}/file", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content == b"hello world"
    assert resp.headers["content-type"].startswith("text/plain")
    assert "note.txt" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_get_file_unknown_id_404(client, auth_headers):
    assert (await client.get("/documents/9999/file", headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_get_file_missing_on_disk_404(client, db, auth_headers, tmp_path, monkeypatch):
    doc = await _document(db, tmp_path, monkeypatch, on_disk=False)
    resp = await client.get(f"/documents/{doc.id}/file", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_file_requires_auth(client, db, tmp_path, monkeypatch):
    doc = await _document(db, tmp_path, monkeypatch)
    assert (await client.get(f"/documents/{doc.id}/file")).status_code == 401


@pytest.mark.asyncio
async def test_get_file_scoped_to_owner(client, db, auth_headers, tmp_path, monkeypatch):
    # Document owned by another user → 404 for this caller.
    doc = await _document(db, tmp_path, monkeypatch, user_id=999)
    resp = await client.get(f"/documents/{doc.id}/file", headers=auth_headers)
    assert resp.status_code == 404
