"""API tests for RAG source management and dashboard stats."""


async def test_drivers(client, auth_headers):
    r = await client.get("/api/rag-sources/drivers", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["key"] == "qdrant"


async def test_create_list_and_bad_driver(client, auth_headers):
    made = await client.post(
        "/api/rag-sources", headers=auth_headers, json={"rag_key": "qdrant", "label": "Main KB", "writable": True}
    )
    assert made.status_code == 201
    assert len((await client.get("/api/rag-sources", headers=auth_headers)).json()) == 1

    bad = await client.post("/api/rag-sources", headers=auth_headers, json={"rag_key": "nope", "label": "x"})
    assert bad.status_code == 400


async def test_patch_and_delete(client, auth_headers):
    src_id = (
        await client.post("/api/rag-sources", headers=auth_headers, json={"rag_key": "qdrant", "label": "KB"})
    ).json()["id"]
    patched = await client.patch(f"/api/rag-sources/{src_id}", headers=auth_headers, json={"enabled": False})
    assert patched.json()["enabled"] is False
    assert (await client.delete(f"/api/rag-sources/{src_id}", headers=auth_headers)).status_code == 204


async def test_stats(client, auth_headers):
    r = await client.get("/api/rag-sources/stats", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_documents"] == 0
    assert body["total_chunks"] == 0
