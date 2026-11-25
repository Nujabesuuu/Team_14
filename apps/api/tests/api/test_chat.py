from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import finish_and_count, match_via_feedback, seed_games


async def _matched(client, make_user):
    games = await seed_games()
    a, a_h = await make_user()
    b, b_h = await make_user()
    event = await finish_and_count(client, a_h, b_h, games["valorant"])
    match_id = await match_via_feedback(client, event["id"], a_h, a["id"], b_h, b["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=a_h)).json()["conversation_id"]
    return a, a_h, b, b_h, conv_id


async def test_history_is_private_and_ordered(client, make_user):
    a, a_h, b, b_h, conv_id = await _matched(client, make_user)
    _, outsider_h = await make_user()
    r = await client.get(f"/conversations/{conv_id}/messages", headers=outsider_h)
    assert r.status_code == 403 and r.json()["code"] == "NOT_YOUR_CONVERSATION"

    for body in ("gg", "wp", "again?"):
        r = await client.post(f"/conversations/{conv_id}/messages", headers=a_h, json={"body": body})
        assert r.status_code == 201
    r = await client.get(f"/conversations/{conv_id}/messages", headers=b_h)
    assert [m["body"] for m in r.json()] == ["gg", "wp", "again?"]
    assert (await client.get("/matches", headers=b_h)).json()[0]["last_message"]["body"] == "again?"

    r = await client.post(f"/conversations/{conv_id}/messages", headers=a_h, json={"body": "   "})
    assert r.status_code == 422


# --- WebSocket tests run entirely inside the sync TestClient (its own event loop/thread). ---


async def test_websocket_delivers_to_both_sides(client, make_user):
    # The match is set up through the async client: a counted game needs its start time moved in the DB (US-07).
    _, a_h, _, b_h, conv_id = await _matched(client, make_user)
    token_a, token_b = (h["Authorization"].removeprefix("Bearer ") for h in (a_h, b_h))
    with TestClient(app) as tc:
        with (
            tc.websocket_connect(f"/api/v1/ws?token={token_a}") as ws_a,
            tc.websocket_connect(f"/api/v1/ws?token={token_b}") as ws_b,
        ):
            ws_a.send_json({"type": "message.send", "conversation_id": conv_id, "body": "hello from A"})
            got_b = ws_b.receive_json()
            got_a = ws_a.receive_json()
            assert got_b["type"] == "message.new" and got_b["message"]["body"] == "hello from A"
            assert got_a["message"]["id"] == got_b["message"]["id"]

            ws_a.send_json({"type": "message.send", "conversation_id": "not-a-uuid", "body": "x"})
            assert ws_a.receive_json()["code"] == "BAD_CONVERSATION_ID"

            ws_a.send_json({"type": "ping"})
            assert ws_a.receive_json() == {"type": "pong"}

        r = tc.get(f"/api/v1/conversations/{conv_id}/messages", headers={"Authorization": f"Bearer {token_b}"})
        assert [m["body"] for m in r.json()] == ["hello from A"]


def test_websocket_rejects_bad_token():
    with TestClient(app) as tc:
        try:
            with tc.websocket_connect("/api/v1/ws?token=bad"):
                raise AssertionError("should have been closed")
        except Exception as exc:  # noqa: BLE001 - starlette raises WebSocketDisconnect
            assert exc.__class__.__name__ == "WebSocketDisconnect"
