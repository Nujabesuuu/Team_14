async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_health_db_runs_a_query(client):
    r = await client.get("/health/db")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "sqlite"}


async def test_validation_error_uses_error_envelope(client):
    r = await client.post("/auth/register", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert isinstance(body["detail"], str)
    assert {f["field"] for f in body["fields"]} >= {"email", "password", "display_name", "birth_date"}


async def test_unknown_route_uses_error_envelope(client):
    r = await client.get("/no-such-route")
    assert r.status_code == 404
    assert r.json() == {"code": "NOT_FOUND", "detail": "Not Found"}
