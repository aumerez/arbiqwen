"""API tests for chat CRUD and streaming fallback."""


async def _new_chat(client, auth_headers, title="First"):
    return (await client.post("/chats", headers=auth_headers, json={"title": title})).json()


async def test_create_and_list(client, auth_headers):
    chat = await _new_chat(client, auth_headers)
    assert chat["title"] == "First"
    listing = await client.get("/chats", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_stream_fallback_and_persist(client, auth_headers):
    chat = await _new_chat(client, auth_headers)
    r = await client.post(f"/chats/{chat['id']}/messages", headers=auth_headers, json={"message": "hi"})
    assert r.status_code == 200
    # No LLM key configured -> graceful fallback + done event.
    assert "not configured" in r.text
    assert '"type": "done"' in r.text

    msgs = await client.get(f"/chats/{chat['id']}/messages", headers=auth_headers)
    roles = [m["role"] for m in msgs.json()]
    assert roles == ["user", "assistant"]


async def test_generate_title(client, auth_headers):
    chat = await _new_chat(client, auth_headers)
    r = await client.post(f"/chats/{chat['id']}/generate-title", headers=auth_headers, json={"message": "reset a report"})
    assert r.status_code == 200
    assert r.json()["title"]


async def test_stream_requires_auth(client, auth_headers):
    chat = await _new_chat(client, auth_headers)
    r = await client.post(f"/chats/{chat['id']}/messages", json={"message": "hi"})
    assert r.status_code == 401


async def test_missing_chat_404(client, auth_headers):
    assert (await client.get("/chats/999", headers=auth_headers)).status_code == 404


async def test_delete_chat(client, auth_headers):
    chat = await _new_chat(client, auth_headers)
    assert (await client.delete(f"/chats/{chat['id']}", headers=auth_headers)).status_code == 204
