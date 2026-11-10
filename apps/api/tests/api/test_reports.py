"""US-09 «Поскаржитись» and US-10 «Рішення модератора», end to end through the public API."""

import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta

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
    games, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    await onboard(client, dara_h, games=[games["valorant"]])
    await onboard(client, maks_h, games=[games["valorant"]])
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]

    marker = "zebra-crossing-42"
    r = await client.post("/reports", headers=dara_h, json=_report(maks, "chat", conv_id, comment=marker))
    assert r.status_code == 201
    report_id = r.json()["id"]
    assert "reporter" not in r.json()

    # Everything the reported person can read: no trace of the report, its text or its id.
    assert (await client.get("/reports/mine", headers=maks_h)).json() == []
    for path in (
        "/me",
        "/matches",
        f"/matches/{match_id}",
        f"/conversations/{conv_id}/messages",
        "/events?mine=true",
        f"/events/{event['id']}",
        "/discover?mode=duo",
        "/moderation/reports",
    ):
        body = (await client.get(path, headers=maks_h)).text
        assert marker not in body and report_id not in body and "report" not in body.lower(), path


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


# --- Found by the AI code review of PR #2 ---


async def test_moderator_cannot_decide_a_report_they_are_part_of(client, make_user):
    games = await seed_games()
    dara, dara_h = await make_user(display_name="Dara")
    mod, mod_h = await _moderator(make_user)
    _, other_mod_h = await _moderator(make_user)
    event = await play_together(client, mod_h, dara_h, games["valorant"])

    about_mod = (await client.post("/reports", headers=dara_h, json=_report(mod, "event", event["id"]))).json()["id"]
    by_mod = (await client.post("/reports", headers=mod_h, json=_report(dara, "event", event["id"]))).json()["id"]

    for report_id, decision in ((about_mod, "dismissed"), (about_mod, "banned"), (by_mod, "banned")):
        r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": decision})
        assert r.status_code == 403 and r.json()["code"] == "REPORT_CONFLICT_OF_INTEREST", (report_id, decision)
    assert (await client.get("/me", headers=mod_h)).status_code == 200

    # Another moderator can still handle both.
    r = await client.post(f"/moderation/reports/{about_mod}/decision", headers=other_mod_h, json={"decision": "warned"})
    assert r.status_code == 200


async def test_second_ban_keeps_the_first_ban_time(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    first = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]
    second = (await client.post("/reports", headers=dara_h, json=_report(maks, "photo", match_id))).json()["id"]

    assert (
        await client.post(f"/moderation/reports/{first}/decision", headers=mod_h, json={"decision": "banned"})
    ).status_code == 200
    banned_at = await _banned_at(maks["id"])
    assert banned_at is not None
    assert (
        await client.post(f"/moderation/reports/{second}/decision", headers=mod_h, json={"decision": "banned"})
    ).status_code == 200
    assert await _banned_at(maks["id"]) == banned_at


async def test_banned_person_is_gone_for_the_people_they_matched(client, make_user):
    games, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    lena, lena_h = await make_user(display_name="Lena")
    for headers in (dara_h, maks_h, lena_h):
        await onboard(client, headers, games=[games["valorant"]])
    match_id = await match_via_feedback(client, event["id"], dara_h, dara["id"], maks_h, maks["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=dara_h)).json()["conversation_id"]
    # Max liked Lena before the ban; her like back must not turn into a match afterwards.
    r = await client.post("/swipes", headers=maks_h, json={"to_user_id": lena["id"], "direction": "right"})
    assert r.status_code == 200 and r.json()["match_created"] is False

    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "chat", conv_id))).json()["id"]
    r = await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "banned"})
    assert r.status_code == 200

    assert (await client.get("/matches", headers=dara_h)).json() == []
    r = await client.post(f"/conversations/{conv_id}/messages", headers=dara_h, json={"body": "still there?"})
    assert r.status_code == 403 and r.json()["code"] == "BLOCKED"
    assert (await client.get(f"/conversations/{conv_id}/messages", headers=dara_h)).status_code == 403

    r = await client.post("/swipes", headers=lena_h, json={"to_user_id": maks["id"], "direction": "right"})
    assert r.status_code == 404 and r.json()["code"] == "USER_NOT_FOUND"
    assert (await client.get("/matches", headers=lena_h)).json() == []


async def test_no_match_with_someone_banned_after_the_game(client, make_user):
    _, dara, dara_h, maks, maks_h, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    r = await client.post(
        f"/events/{event['id']}/feedback", headers=maks_h, json={"to_user_id": dara["id"], "answer": "closer"}
    )
    assert r.status_code == 200 and r.json()["match_created"] is False
    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]
    await client.post(f"/moderation/reports/{report_id}/decision", headers=mod_h, json={"decision": "banned"})

    assert (await client.get(f"/events/{event['id']}/feedback", headers=dara_h)).json()["pending"] == []
    r = await client.post(
        f"/events/{event['id']}/feedback", headers=dara_h, json={"to_user_id": maks["id"], "answer": "closer"}
    )
    assert r.status_code == 200 and r.json()["match_created"] is False
    assert (await client.get("/matches", headers=dara_h)).json() == []


async def test_moderator_does_not_get_photos(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    _, mod_h = await _moderator(make_user)
    await _set_photo(maks["id"], "/media/secret.jpg")
    await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))

    item = (await client.get("/moderation/reports", headers=mod_h)).json()[0]
    assert item["reported"]["photo_url"] is None and item["reporter"]["photo_url"] is None
    assert "secret.jpg" not in (await client.get("/moderation/reports", headers=mod_h)).text


async def test_two_moderators_deciding_at_once_produce_one_decision(client, make_user):
    _, _, dara_h, maks, _, event = await _played(client, make_user)
    mod_a, mod_a_h = await _moderator(make_user)
    mod_b, mod_b_h = await _moderator(make_user)
    report_id = (await client.post("/reports", headers=dara_h, json=_report(maks, "event", event["id"]))).json()["id"]

    url = f"/moderation/reports/{report_id}/decision"
    results = await asyncio.gather(
        client.post(url, headers=mod_a_h, json={"decision": "warned"}),
        client.post(url, headers=mod_b_h, json={"decision": "dismissed"}),
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    winner = next(r for r in results if r.status_code == 200).json()
    loser = next(r for r in results if r.status_code == 409).json()
    assert loser["code"] == "REPORT_ALREADY_DECIDED"

    stored = (await client.get("/moderation/reports", headers=mod_a_h)).json()[0]
    assert stored["status"] == winner["status"] and stored["moderator"]["id"] == winner["moderator"]["id"]


async def test_database_refuses_a_second_open_report_for_the_same_case():
    """The service checks first, but a double tap races it: the unique index is the real guard."""
    from sqlalchemy.exc import IntegrityError

    from app.core.db import SessionLocal
    from app.models import Profile, Report, ReportContext, ReportReason, ReportStatus, User

    async with SessionLocal() as s:
        a = User(email="a@t.dev", password_hash="x", display_name="A", birth_date=date(2000, 1, 1), profile=Profile())
        b = User(email="b@t.dev", password_hash="x", display_name="B", birth_date=date(2000, 1, 1), profile=Profile())
        s.add_all([a, b])
        await s.flush()
        case = {"reporter_id": a.id, "reported_id": b.id, "context": ReportContext.event, "context_id": uuid.uuid4()}
        s.add(Report(**case, reason=ReportReason.spam, status=ReportStatus.warned))
        s.add(Report(**case, reason=ReportReason.spam))
        await s.flush()  # a decided one and an open one may coexist
        s.add(Report(**case, reason=ReportReason.other))
        try:
            await s.flush()
            raise AssertionError("second open report was accepted")
        except IntegrityError:
            await s.rollback()


def test_ban_closes_open_sockets_and_updates_the_lobby():
    """Live effect of the decision: the banned tab is dropped, the host sees the seat free up."""
    with TestClient(app) as tc:
        game_id = tc.portal.call(_seed_one_game)
        dara, dara_h, dara_token = _sync_user(tc, "live-dara@test.dev")
        maks, maks_h, maks_token = _sync_user(tc, "live-max@test.dev")
        mod, mod_h, _ = _sync_user(tc, "live-mod@test.dev")
        tc.portal.call(make_moderator, mod["id"])

        played = _sync_event(tc, dara_h, game_id, "Played together")
        assert tc.post(f"/api/v1/events/{played}/join", headers=maks_h).status_code == 200
        upcoming = _sync_event(tc, dara_h, game_id, "Next week")
        assert tc.post(f"/api/v1/events/{upcoming}/join", headers=maks_h).status_code == 200
        report = tc.post(
            "/api/v1/reports",
            headers=dara_h,
            json={"reported_id": maks["id"], "context": "event", "context_id": played, "reason": "harassment"},
        )
        assert report.status_code == 201, report.text

        with (
            tc.websocket_connect(f"/api/v1/ws?token={maks_token}") as ws_maks,
            tc.websocket_connect(f"/api/v1/ws?token={dara_token}") as ws_dara,
        ):
            r = tc.post(
                f"/api/v1/moderation/reports/{report.json()['id']}/decision", headers=mod_h, json={"decision": "banned"}
            )
            assert r.status_code == 200, r.text

            try:
                ws_maks.receive_json()
                raise AssertionError("the banned socket should have been closed")
            except Exception as exc:  # noqa: BLE001 - starlette raises WebSocketDisconnect
                assert exc.__class__.__name__ == "WebSocketDisconnect" and exc.code == 4403

            updates = {}
            for _ in range(2):
                msg = ws_dara.receive_json()
                assert msg["type"] == "event.updated"
                updates[msg["event"]["id"]] = msg["event"]
            assert {p["id"] for p in updates[upcoming]["participants"]} == {dara["id"]}
            assert {p["id"] for p in updates[played]["participants"]} == {dara["id"]}


def _sync_user(tc: TestClient, email: str) -> tuple[dict, dict[str, str], str]:
    r = tc.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123", "display_name": email.split("@")[0], "birth_date": "2000-01-01"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return r.json()["user"], {"Authorization": f"Bearer {token}"}, token


def _sync_event(tc: TestClient, headers: dict[str, str], game_id: str, title: str) -> str:
    r = tc.post(
        "/api/v1/events",
        headers=headers,
        json={
            "game_id": game_id,
            "title": title,
            "starts_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "max_slots": 2,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _seed_one_game() -> str:
    return str((await seed_games())["valorant"].id)


async def _banned_at(user_id: str):
    from app.core.db import SessionLocal
    from app.models import User

    async with SessionLocal() as s:
        return (await s.get(User, uuid.UUID(user_id))).banned_at


async def _set_photo(user_id: str, url: str) -> None:
    from app.core.db import SessionLocal
    from app.models import User

    async with SessionLocal() as s:
        (await s.get(User, uuid.UUID(user_id))).profile.photo_url = url
        await s.commit()
