from datetime import date

PAYLOAD = {"email": "nika@teamate.dev", "password": "secret123", "display_name": "Nika", "birth_date": "2001-05-05"}


async def test_register_returns_token_and_profile(client):
    r = await client.post("/auth/register", json=PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["email"] == "nika@teamate.dev"

    me = await client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["profile"]["onboarded"] is False


async def test_duplicate_email_conflicts(client):
    await client.post("/auth/register", json=PAYLOAD)
    r = await client.post("/auth/register", json={**PAYLOAD, "email": "NIKA@teamate.dev"})
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_TAKEN"


async def test_login(client):
    await client.post("/auth/register", json=PAYLOAD)
    ok = await client.post("/auth/login", json={"email": PAYLOAD["email"], "password": "secret123"})
    assert ok.status_code == 200
    bad = await client.post("/auth/login", json={"email": PAYLOAD["email"], "password": "wrong"})
    assert bad.status_code == 401 and bad.json()["code"] == "INVALID_CREDENTIALS"


async def test_me_requires_token(client):
    assert (await client.get("/me")).status_code == 401
    r = await client.get("/me", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


async def test_children_cannot_register(client):
    r = await client.post("/auth/register", json={**PAYLOAD, "birth_date": date.today().isoformat()})
    assert r.status_code == 422 and r.json()["code"] == "TOO_YOUNG"
