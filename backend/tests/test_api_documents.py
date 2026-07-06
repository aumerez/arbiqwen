"""API tests for document upload, listing, and folders."""


def _txt(name="sample.txt", body=b"First para.\n\nSecond para here.\n"):
    return {"file": (name, body, "text/plain")}


async def test_upload_and_list(client, auth_headers):
    r = await client.post("/documents/upload", headers=auth_headers, files=_txt(), data={"folder_path": "reports/q3"})
    assert r.status_code == 201
    doc = r.json()
    assert doc["status"] == "indexed"
    assert doc["folder_path"] == "reports/q3"

    listing = await client.get("/documents/", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


async def test_upload_requires_auth(client):
    r = await client.post("/documents/upload", files=_txt())
    assert r.status_code == 401


async def test_upload_unsupported_type(client, auth_headers):
    r = await client.post("/documents/upload", headers=auth_headers, files={"file": ("x.zip", b"x", "application/zip")})
    assert r.status_code == 400


async def test_folders_tree(client, auth_headers):
    await client.post("/documents/upload", headers=auth_headers, files=_txt(), data={"folder_path": "reports/q3"})
    r = await client.get("/documents/folders", headers=auth_headers)
    assert r.status_code == 200
    tree = r.json()
    assert tree[0]["name"] == "reports"
    assert tree[0]["children"][0]["name"] == "q3"


async def test_get_and_delete(client, auth_headers):
    doc_id = (await client.post("/documents/upload", headers=auth_headers, files=_txt())).json()["id"]
    assert (await client.get(f"/documents/{doc_id}", headers=auth_headers)).status_code == 200
    assert (await client.delete(f"/documents/{doc_id}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/documents/{doc_id}", headers=auth_headers)).status_code == 404


async def test_supported_types(client, auth_headers):
    r = await client.get("/documents/supported-types", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 7
