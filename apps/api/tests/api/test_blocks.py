from tests.helpers import create_event, finish_and_count, match_via_feedback, onboard, seed_games


async def test_block_hides_everywhere(client, make_user):
    games = await seed_games()
    me, me_h = await make_user()
    them, them_h = await make_user()
    await onboard(client, me_h, games=[games["valorant"]])
    await onboard(client, them_h, games=[games["valorant"]])

    event = await finish_and_count(client, them_h, me_h, games["valorant"])
    match_id = await match_via_feedback(client, event["id"], me_h, me["id"], them_h, them["id"])
    conv_id = (await client.get(f"/matches/{match_id}", headers=me_h)).json()["conversation_id"]
    their_event = await create_event(client, them_h, games["valorant"], title="Another one")

    r = await client.post("/blocks", headers=me_h, json={"user_id": them["id"]})
    assert r.status_code == 204

    assert them["id"] not in [
        c["user"]["id"] for c in (await client.get("/discover?mode=duo", headers=me_h)).json()["cards"]
    ]
    assert their_event["id"] not in [e["id"] for e in (await client.get("/events", headers=me_h)).json()]
    assert (await client.get(f"/conversations/{conv_id}/messages", headers=them_h)).status_code == 403
    r = await client.post(f"/events/{their_event['id']}/join", headers=me_h)
    # NEVER-05: the same answer as for any event the person may not see, so the block itself stays secret.
    assert r.status_code == 403 and r.json()["code"] == "EVENT_NOT_VISIBLE"


async def test_cannot_block_self(client, make_user):
    me, me_h = await make_user()
    r = await client.post("/blocks", headers=me_h, json={"user_id": me["id"]})
    assert r.status_code == 422
