"""API tests for integrations (marketplace, instances) and OAuth linkage."""


async def test_marketplace(client, auth_headers):
    r = await client.get("/api/integrations/marketplace", headers=auth_headers)
    assert r.status_code == 200
    keys = {t["key"] for t in r.json()["tiles"]}
    assert {"slack", "github", "google_drive", "webhook"} <= keys


async def test_connect_list_dup_and_unknown(client, auth_headers):
    r = await client.post(
        "/api/integrations/slack/connect",
        headers=auth_headers,
        json={"alias": "Team Slack", "config": {"bot_token": "x"}},
    )
    assert r.status_code == 201

    listing = await client.get("/api/integrations/", headers=auth_headers)
    assert len(listing.json()["instances"]) == 1

    dup = await client.post("/api/integrations/slack/connect", headers=auth_headers, json={"alias": "Team Slack", "config": {}})
    assert dup.status_code == 409

    unknown = await client.post("/api/integrations/nope/connect", headers=auth_headers, json={"alias": "x", "config": {}})
    assert unknown.status_code == 400


async def test_instance_update_and_delete(client, auth_headers):
    inst_id = (
        await client.post("/api/integrations/webhook/connect", headers=auth_headers, json={"alias": "Hook", "config": {}})
    ).json()["id"]
    renamed = await client.put(f"/api/integrations/instances/{inst_id}", headers=auth_headers, json={"alias": "Hook2"})
    assert renamed.json()["instance_alias"] == "Hook2"
    assert (await client.delete(f"/api/integrations/instances/{inst_id}", headers=auth_headers)).status_code == 204


async def test_integrations_config(client, auth_headers):
    r = await client.get("/integrations-config", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["tiles"]) == 4


async def test_oauth_linkage(client, auth_headers, db):
    from app.integrations.oauth_models import OAuthToken

    db.add(OAuthToken(tenant_id=1, user_id=1, provider="google", access_token="tok", scopes="drive.readonly"))
    await db.commit()

    linked = await client.get("/api/integrations/oauth/linked-integrations", headers=auth_headers)
    assert linked.json()["linked_integrations"][0]["provider"] == "google"

    ok = await client.get("/api/integrations/oauth/status?provider=google&scopes=drive.readonly", headers=auth_headers)
    assert ok.json()["linked"] is True

    missing = await client.get("/api/integrations/oauth/status?provider=google&scopes=calendar", headers=auth_headers)
    assert missing.json()["linked"] is False

    disconnected = await client.post("/api/integrations/oauth/google/disconnect", headers=auth_headers)
    assert disconnected.json()["disconnected"] is True
    assert (await client.get("/api/integrations/oauth/linked-integrations", headers=auth_headers)).json()[
        "linked_integrations"
    ] == []
