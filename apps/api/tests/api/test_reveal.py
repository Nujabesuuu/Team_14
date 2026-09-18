from tests.helpers import match_via_feedback, play_together, seed_games


async def _matched_pair(client, make_user):
    games = await seed_games()
    a, a_h = await make_user()
    b, b_h = await make_user()
    event = await play_together(client, a_h, b_h, games["valorant"])
    match_id = await match_via_feedback(client, event["id"], a_h, a["id"], b_h, b["id"])
    return games, a, a_h, b, b_h, match_id


async def test_consent_needs_both(client, make_user):
    _, a, a_h, b, b_h, match_id = await _matched_pair(client, make_user)
    r = await client.post(f"/matches/{match_id}/reveal/consent", headers=a_h)
    assert r.json()["reveal"] == {
        "my_stage": 1,
        "their_stage": 1,
        "my_consent": True,
        "their_consent": False,
        "early_request_from_me": False,
        "early_request_from_them": False,
    }
    r = await client.post(f"/matches/{match_id}/reveal/consent", headers=b_h)
    assert r.json()["reveal"]["my_stage"] == 3 and r.json()["reveal"]["their_stage"] == 3


async def test_playing_again_after_match_unlocks_stage_two(client, make_user):
    games, a, a_h, b, b_h, match_id = await _matched_pair(client, make_user)
    await play_together(client, b_h, a_h, games["valorant"])
    r = await client.get(f"/matches/{match_id}", headers=a_h)
    assert r.json()["reveal"]["my_stage"] == 2 and r.json()["reveal"]["their_stage"] == 2


async def test_early_reveal_is_premium_and_needs_acceptance(client, make_user):
    _, a, a_h, b, b_h, match_id = await _matched_pair(client, make_user)
    r = await client.post(f"/matches/{match_id}/reveal/early-request", headers=a_h)
    assert r.status_code == 402
    r = await client.post(f"/matches/{match_id}/reveal/early-accept", headers=b_h)
    assert r.status_code == 409 and r.json()["code"] == "NO_EARLY_REQUEST"

    await client.post("/me/premium", headers=a_h, json={"enabled": True})
    r = await client.post(f"/matches/{match_id}/reveal/early-request", headers=a_h)
    assert r.status_code == 200 and r.json()["reveal"]["early_request_from_me"] is True
    r = await client.get(f"/matches/{match_id}", headers=b_h)
    assert r.json()["reveal"]["early_request_from_them"] is True and r.json()["reveal"]["my_stage"] == 1

    r = await client.post(f"/matches/{match_id}/reveal/early-accept", headers=b_h)
    assert r.json()["reveal"]["my_stage"] == 3 and r.json()["reveal"]["their_stage"] == 3
