from tests.helpers import create_event, match_via_feedback, play_together, seed_games


async def test_feedback_needs_finished_event(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    event = await create_event(client, host_h, games["valorant"])
    await client.post(f"/events/{event['id']}/join", headers=guest_h)

    r = await client.post(
        f"/events/{event['id']}/feedback", headers=host_h, json={"to_user_id": guest["id"], "answer": "closer"}
    )
    assert r.status_code == 409 and r.json()["code"] == "EVENT_NOT_FINISHED"


async def test_outsider_cannot_rate(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    _, outsider_h = await make_user()
    event = await play_together(client, host_h, guest_h, games["valorant"])
    r = await client.get(f"/events/{event['id']}/feedback", headers=outsider_h)
    assert r.status_code == 403 and r.json()["code"] == "NOT_PARTICIPANT"


async def test_mutual_closer_creates_one_match(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    event = await play_together(client, host_h, guest_h, games["valorant"])

    pending = await client.get(f"/events/{event['id']}/feedback", headers=host_h)
    assert [p["id"] for p in pending.json()["pending"]] == [guest["id"]]

    match_id = await match_via_feedback(client, event["id"], host_h, host["id"], guest_h, guest["id"])

    for h in (host_h, guest_h):
        matches = (await client.get("/matches", headers=h)).json()
        assert len(matches) == 1 and matches[0]["id"] == match_id
        assert matches[0]["source"] == "post_game"
        assert matches[0]["reveal"]["my_stage"] == 1 and matches[0]["reveal"]["their_stage"] == 1
        assert matches[0]["conversation_id"]

    r = await client.post(
        f"/events/{event['id']}/feedback", headers=host_h, json={"to_user_id": guest["id"], "answer": "closer"}
    )
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_RATED"


async def test_closer_plus_again_is_not_a_match(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    event = await play_together(client, host_h, guest_h, games["valorant"])
    await client.post(
        f"/events/{event['id']}/feedback", headers=host_h, json={"to_user_id": guest["id"], "answer": "closer"}
    )
    r = await client.post(
        f"/events/{event['id']}/feedback", headers=guest_h, json={"to_user_id": host["id"], "answer": "again"}
    )
    assert r.json()["match_created"] is False
    assert (await client.get("/matches", headers=host_h)).json() == []


async def test_match_detail_is_private(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    _, outsider_h = await make_user()
    event = await play_together(client, host_h, guest_h, games["valorant"])
    match_id = await match_via_feedback(client, event["id"], host_h, host["id"], guest_h, guest["id"])
    r = await client.get(f"/matches/{match_id}", headers=outsider_h)
    assert r.status_code == 403 and r.json()["code"] == "NOT_YOUR_MATCH"
