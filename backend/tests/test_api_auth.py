"""API tests for the auth flow."""


async def _login(client, email="tester@arbi.dev", password="secret123"):
    return await client.post("/auth/login", json={"email": email, "password": password})


async def test_login_success(client, user):
    r = await _login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["accessToken"] and body["refreshToken"]
    assert body["user"]["email"] == "tester@arbi.dev"


async def test_login_wrong_password(client, user):
    r = await _login(client, password="nope1234")
    assert r.status_code == 401


async def test_me_requires_token(client):
    assert (await client.get("/auth/me")).status_code == 401


async def test_me_with_token(client, user):
    token = (await _login(client)).json()["accessToken"]
    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "tester@arbi.dev"


async def test_refresh_rotates(client, user):
    refresh = (await _login(client)).json()["refreshToken"]
    r = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert r.json()["accessToken"]
