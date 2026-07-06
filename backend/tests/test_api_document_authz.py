"""Documents must be scoped to their owner (no cross-user access)."""

from app.auth.jwt import create_access_token


def _other_user_headers():
    # A second, distinct user's token (get_current_user decodes without a DB lookup).
    token = create_access_token({"sub": "999", "email": "other@arbi.dev", "tenant_id": 1, "role": "user"})
    return {"Authorization": f"Bearer {token}"}


async def test_documents_are_owner_scoped(client, auth_headers):
    doc_id = (
        await client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("mine.txt", b"secret content", "text/plain")},
            data={"folder_path": "private"},
        )
    ).json()["id"]

    other = _other_user_headers()

    # Owner sees it.
    assert (await client.get("/documents/", headers=auth_headers)).json()["total"] == 1
    assert (await client.get(f"/documents/{doc_id}", headers=auth_headers)).status_code == 200

    # Other user sees nothing and cannot fetch or delete it.
    assert (await client.get("/documents/", headers=other)).json()["total"] == 0
    assert (await client.get("/documents/folders", headers=other)).json() == []
    assert (await client.get(f"/documents/{doc_id}", headers=other)).status_code == 404
    assert (await client.delete(f"/documents/{doc_id}", headers=other)).status_code == 404

    # Still there for the owner.
    assert (await client.get(f"/documents/{doc_id}", headers=auth_headers)).status_code == 200
