from datetime import date

from tests.helpers import onboard, seed_games


async def test_discover_respects_modes_and_swipes(client, make_user):
    games = await seed_games()
    me, me_h = await make_user()
    await onboard(client, me_h, modes=("duo", "dating"), games=[games["valorant"]])

    duo, duo_h = await make_user()
    await onboard(client, duo_h, modes=("duo",), games=[games["valorant"]])
    dating, dating_h = await make_user()
    await onboard(client, dating_h, modes=("dating",), games=[games["dota2"]])
    minor, minor_h = await make_user(birth_date=date(date.today().year - 16, 1, 1))
    await onboard(client, minor_h, modes=("duo",), games=[games["valorant"]])

    r = await client.get("/discover?mode=duo", headers=me_h)
    assert r.status_code == 200
    ids = [c["user"]["id"] for c in r.json()["cards"]]
    assert ids[0] == duo["id"], "highest compatibility first"
    assert set(ids) == {duo["id"], minor["id"]}
    assert r.json()["rights_left"] == 20

    r = await client.get("/discover?mode=dating", headers=me_h)
    assert [c["user"]["id"] for c in r.json()["cards"]] == [dating["id"]]

    r = await client.get("/discover?mode=friends", headers=me_h)
    assert r.status_code == 422 and r.json()["code"] == "MODE_NOT_ENABLED"

    await client.post("/swipes", headers=me_h, json={"to_user_id": duo["id"], "direction": "left"})
    r = await client.get("/discover?mode=duo", headers=me_h)
    assert duo["id"] not in [c["user"]["id"] for c in r.json()["cards"]]


async def test_mutual_like_matches(client, make_user):
    games = await seed_games()
    a, a_h = await make_user()
    b, b_h = await make_user()
    await onboard(client, a_h, games=[games["valorant"]])
    await onboard(client, b_h, games=[games["valorant"]])

    r = await client.post("/swipes", headers=a_h, json={"to_user_id": b["id"], "direction": "right"})
    assert r.json() == {"match_created": False, "match_id": None, "rights_left": 19}
    r = await client.post("/swipes", headers=b_h, json={"to_user_id": a["id"], "direction": "right"})
    assert r.json()["match_created"] is True
    assert (await client.get("/matches", headers=a_h)).json()[0]["source"] == "mutual_like"

    r = await client.post("/swipes", headers=a_h, json={"to_user_id": b["id"], "direction": "right"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_SWIPED"


async def test_free_limit_and_premium(client, make_user):
    games = await seed_games()
    me, me_h = await make_user()
    await onboard(client, me_h, games=[games["valorant"]])
    targets = []
    for _ in range(21):
        u, h = await make_user()
        await onboard(client, h, games=[games["valorant"]])
        targets.append(u)

    for u in targets[:20]:
        r = await client.post("/swipes", headers=me_h, json={"to_user_id": u["id"], "direction": "right"})
        assert r.status_code == 200, r.text
    r = await client.post("/swipes", headers=me_h, json={"to_user_id": targets[20]["id"], "direction": "right"})
    assert r.status_code == 429 and r.json()["code"] == "SWIPE_LIMIT"

    assert (await client.post("/swipes/undo", headers=me_h)).status_code == 402
    assert (await client.get("/likes/incoming", headers=me_h)).status_code == 402

    await client.post("/me/premium", headers=me_h, json={"enabled": True})
    r = await client.post("/swipes", headers=me_h, json={"to_user_id": targets[20]["id"], "direction": "right"})
    assert r.status_code == 200 and r.json()["rights_left"] is None
    assert (await client.post("/swipes/undo", headers=me_h)).status_code == 204
    r = await client.get("/discover?mode=duo", headers=me_h)
    assert targets[20]["id"] in [c["user"]["id"] for c in r.json()["cards"]], "undo puts the card back"


async def test_incoming_likes_for_premium(client, make_user):
    games = await seed_games()
    me, me_h = await make_user(premium=True)
    fan, fan_h = await make_user()
    await onboard(client, me_h, games=[games["valorant"]])
    await onboard(client, fan_h, games=[games["valorant"]])
    await client.post("/swipes", headers=fan_h, json={"to_user_id": me["id"], "direction": "right"})
    r = await client.get("/likes/incoming", headers=me_h)
    assert [c["user"]["id"] for c in r.json()] == [fan["id"]]
