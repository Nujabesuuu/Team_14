"""US-09 «Поскаржитись» and US-10 «Рішення модератора», end to end through the public API."""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import create_event, make_moderator, match_via_feedback, onboard, play_together, seed_games


async def _played(client, make_user):
    """Dara and Max played one event together; Max hosted."""
    games = await seed_games()
    dara, dara_h = await make_user(display_name="Dara")
    maks, maks_h = await make_user(display_name="Max")
    event = await play_together(client, maks_h, dara_h, games["valorant"])
    return games, dara, dara_h, maks, maks_h, event


async def _moderator(make_user):
    mod, mod_h = await make_user(display_name="Iryna")
    await make_moderator(mod["id"])
    return mod, mod_h


def _report(reported, context, context_id, reason="harassment", **extra) -> dict:
    return {"reported_id": reported["id"], "context": context, "context_id": context_id, "reason": reason, **extra}


# --- US-09 ---


async def test_report_from_event_is_confirmed_and_listed(client, make_user):
    _, dara, dara_h, maks, _, event = await _played(client, make_user)

    r = await client.post(
        "/reports", headers=dara_h, json=_report(maks, "event", event["id"], comment="slurs in voice")
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "new" and body["decided_at"] is None
    assert body["reported"]["id"] == maks["id"] and body["context"] == "event" and body["reason"] == "harassment"

    mine = (await client.get("/reports/mine", headers=dara_h)).json()
    assert [m["id"] for m in mine] == [body["id"]]


async def test_report_from_chat_and_from_photo(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]

    r = await client.post("/reports", headers=dara_h, json=_report(maks, "chat", conv_id, reason="spam"))
    assert r.status_code == 201, r.text
    r = await client.post(
        "/reports", headers=dara_h, json=_report(maks, "photo", match_id, reason="inappropriate_photo")
    )
    assert r.status_code == 201, r.text
    assert {m["context"] for m in (await client.get("/reports/mine", headers=dara_h)).json()} == {"chat", "photo"}


async def test_blocking_someone_does_not_stop_the_report(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]
    assert (await client.post("/blocks", headers=dara_h, json={"user_id": maks["id"]})).status_code == 204

    r = await client.post("/reports", headers=dara_h, json=_report(maks, "chat", conv_id))
    assert r.status_code == 201, r.text


async def test_reason_is_required_and_comment_is_limited(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    no_reason = {"reported_id": maks["id"], "context": "event", "context_id": event["id"]}

    r = await client.post("/reports", headers=dara_h, json=no_reason)
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    assert "reason" in {f["field"] for f in r.json()["fields"]}

    r = await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"], comment="x" * 501))
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    r = await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"], comment="x" * 500))
    assert r.status_code == 201

    assert (await client.post("/reports", json=no_reason)).status_code == 401


async def test_cannot_report_yourself(client, make_user):
    _, dara, dara_h, _, _, event = await _played(client, make_user)
    r = await client.post("/reports", headers=dara_h, json=_report(dara, "event", event["id"]))
    assert r.status_code == 422 and r.json()["code"] == "CANNOT_REPORT_SELF"


async def test_report_needs_a_shared_context_and_reveals_nothing_else(client, make_user):
    games, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    stranger, stranger_h = await make_user(display_name="Stranger")
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]
    other_event = await create_event(client, maks_h, games["valorant"], title="Without Dara")

    attempts = [
        (stranger_h, _report(maks, "event", event["id"])),  # reporter was not in the event
        (stranger_h, _report(maks, "chat", conv_id)),  # someone else's conversation
        (stranger_h, _report(maks, "photo", match_id)),  # someone else's match
        (dara_h, _report(maks, "event", other_event["id"])),  # reporter never joined this one
        (dara_h, _report(stranger, "event", event["id"])),  # reported person was not there
        (dara_h, _report(maks, "event", str(uuid.uuid4()))),  # no such event
        (dara_h, _report({"id": str(uuid.uuid4())}, "event", event["id"])),  # no such account
        (dara_h, _report(maks, "chat", event["id"])),  # id of the wrong kind
    ]
    for headers, payload in attempts:
        r = await client.post("/reports", headers=headers, json=payload)
        assert r.status_code == 422 and r.json()["code"] == "REPORT_CONTEXT_INVALID", (payload, r.text)


async def test_one_open_report_per_person_and_context(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    payload = _report(maks, "event", event["id"])

    first = await client.post("/reports", headers=dara_h, json=payload)
    assert first.status_code == 201
    again = await client.post("/reports", headers=dara_h, json={**payload, "reason": "spam"})
    assert again.status_code == 409 and again.json()["code"] == "ALREADY_REPORTED"

    r = await client.post(
        f"/moderation/reports/{first.json()['id']}/decision", headers=mod_h, json={"decision": "warned"}
    )
    assert r.status_code == 200
    assert (await client.post("/reports", headers=dara_h, json=payload)).status_code == 201


async def test_reported_person_never_learns_who_reported(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    r = await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))
    assert r.status_code == 201
    assert "reporter" not in r.json()

    assert (await client.get("/reports/mine", headers=maks_h)).json() == []
    r = await client.get("/moderation/reports", headers=maks_h)
    assert r.status_code == 403 and dara["id"] not in r.text


# --- US-10 ---


async def test_queue_is_for_moderators_only(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]

    r = await client.get("/moderation/reports", headers=dara_h)
    assert r.status_code == 403 and r.json()["code"] == "MODERATOR_ONLY"
    # Same answer for a real and a made-up id: a player cannot probe which reports exist.
    for target in (report_id, uuid.uuid4()):
        r = await client.post(f"/moderation/reports/{target}/decision", headers=dara_h, json={"decision": "banned"})
        assert r.status_code == 403 and r.json()["code"] == "MODERATOR_ONLY"
    assert (await client.get("/moderation/reports")).status_code == 401

    me = (await client.get("/me", headers=dara_h)).json()
    assert me["user"]["role"] == "user"


async def test_moderator_sees_context_and_decides_once(client, make_user):
    _, dara, dara_h, maks, _, event = await _played(client, make_user)
    mod, mod_h = await _moderator(make_user)
    assert (await client.get("/me", headers=mod_h)).json()["user"]["role"] == "moderator"
    assert (await client.get("/moderation/reports?status=new", headers=mod_h)).json() == []

    payload = _report(maks, "event", event["id"], comment="slurs in voice")
    report_id = (await client.post("/reports", headers=dara_h, json=payload)).json()["id"]

    queue = (await client.get("/moderation/reports?status=new", headers=mod_h)).json()
    assert len(queue) == 1
    item = queue[0]
    assert item["id"] == report_id and item["status"] == "new"
    assert item["reporter"]["id"] == dara["id"] and item["reported"]["id"] == maks["id"]
    assert item["context"] == "event" and item["context_id"] == event["id"]
    assert item["context_label"] == "Valorant · Duo tonight"
    assert item["reason"] == "harassment" and item["comment"] == "slurs in voice" and item["created_at"]
    assert item["moderator"] is None and item["decided_at"] is None

    r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "warned"})
    assert r.status_code == 200, r.text
    decided = r.json()
    assert decided["status"] == "warned" and decided["moderator"]["id"] == mod["id"] and decided["decided_at"]

    assert (await client.get("/moderation/reports?status=new", headers=mod_h)).json() == []
    assert [i["status"] for i in (await client.get("/moderation/reports", headers=mod_h)).json()] == ["warned"]

    mine = (await client.get("/reports/mine", headers=dara_h)).json()
    assert mine[0]["status"] == "warned" and mine[0]["decided_at"]

    r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "banned"})
    assert r.status_code == 409 and r.json()["code"] == "REPORT_ALREADY_DECIDED"
    r = await client.post(f"/moderation/reports/{uuid.uuid4()}/decision", headers=mod_h, json={"decision": "warned"})
    assert r.status_code == 404 and r.json()["code"] == "REPORT_NOT_FOUND"


async def test_decision_must_be_a_real_decision(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]

    for bad in ("new", "deleted", ""):
        r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": bad})
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR", bad


async def test_chat_report_is_labelled_for_the_moderator(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]
    await client.post("/reports", headers=dara_h, json=_report(maks, "chat", conv_id))
    await client.post("/reports", headers=dara_h, json=_report(maks, "photo", match_id))

    labels = {i["context"]: i["context_label"] for i in (await client.get("/moderation/reports", headers=mod_h)).json()}
    assert labels == {"chat": "Chat between Dara and Max", "photo": "Photo of Max"}


async def test_ban_locks_the_account_out(client, make_user):
    _, _, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]
    assert (await client.get("/me", headers=maks_h)).status_code == 200

    r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "banned"})
    assert r.status_code == 200 and r.json()["status"] == "banned"

    # The session that was already open stops working on every endpoint, not only on login.
    for path in ("/me", "/events", "/matches", "/reports/mine"):
        r = await client.get(path, headers=maks_h)
        assert r.status_code == 403 and r.json()["code"] == "ACCOUNT_BANNED", path

    r = await client.post("/auth/login", json={"email": maks["email"], "password": "secret123"})
    assert r.status_code == 403 and r.json()["code"] == "ACCOUNT_BANNED"
    r = await client.post("/auth/login", json={"email": maks["email"], "password": "wrong-password"})
    assert r.status_code == 401 and r.json()["code"] == "INVALID_CREDENTIALS"

    assert (await client.get("/me", headers=dara_h)).status_code == 200


async def test_ban_removes_the_person_from_upcoming_events_and_discover(client, make_user):
    games, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    await onboard(client, dara_h, games=[games["valorant"]])
    await onboard(client, maks_h, games=[games["valorant"]])
    hosted = await create_event(client, maks_h, games["valorant"], title="Max hosts")
    joined = await create_event(client, dara_h, games["valorant"], title="Dara hosts")
    assert (await client.post(f"/events/{joined['id']}/join", headers=maks_h)).json()["status"] == "full"
    assert maks["id"] in [
        c["user"]["id"] for c in (await client.get("/discover?mode=duo", headers=dara_h)).json()["cards"]
    ]

    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]
    r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "banned"})
    assert r.status_code == 200

    assert (await client.get(f"/events/{hosted['id']}", headers=dara_h)).json()["status"] == "cancelled"
    freed = (await client.get(f"/events/{joined['id']}", headers=dara_h)).json()
    assert freed["status"] == "open" and [p["id"] for p in freed["participants"]] == [dara["id"]]
    # History stays: the finished event they played is evidence for the report.
    assert maks["id"] in [
        p["id"] for p in (await client.get(f"/events/{event['id']}", headers=dara_h)).json()["participants"]
    ]
    assert maks["id"] not in [
        c["user"]["id"] for c in (await client.get("/discover?mode=duo", headers=dara_h)).json()["cards"]
    ]


async def test_warning_and_dismissal_do_not_lock_anyone_out(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])

    first = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]
    second = (await client.post("/reports", headers=dara_h, json=_report(maks, "photo", match_id))).json()["id"]
    await client.post(f"/moderation/reports/{first}/decision", headers=mod_h, json={"decision": "warned"})
    await client.post(f"/moderation/reports/{second}/decision", headers=mod_h, json={"decision": "dismissed"})

    assert (await client.get("/me", headers=maks_h)).status_code == 200
    assert {m["status"] for m in (await client.get("/reports/mine", headers=dara_h)).json()} == {"warned", "dismissed"}


def test_banned_account_cannot_open_a_websocket():
    with TestClient(app) as tc:
        r = tc.post(
            "/api/v1/auth/register",
            json={
                "email": "ws-ban@test.dev",
                "password": "secret123",
                "display_name": "Ban",
                "birth_date": "2000-01-01",
            },
        )
        token, user_id = r.json()["access_token"], r.json()["user"]["id"]
        with tc.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            ws.send_json({"type": "ping"})
            assert ws.receive_json() == {"type": "pong"}

        tc.portal.call(_ban_directly, user_id)
        try:
            with tc.websocket_connect(f"/api/v1/ws?token={token}"):
                raise AssertionError("should have been closed")
        except Exception as exc:  # noqa: BLE001 - starlette raises WebSocketDisconnect
            assert exc.__class__.__name__ == "WebSocketDisconnect" and exc.code == 4403


async def _ban_directly(user_id: str) -> None:
    from app.core.db import SessionLocal
    from app.models import User
    from app.models._base import utcnow

    async with SessionLocal() as s:
        user = await s.get(User, uuid.UUID(user_id))
        user.banned_at = utcnow()
        await s.commit()
