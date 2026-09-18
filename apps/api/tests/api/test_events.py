from datetime import date

from tests.helpers import create_event, onboard, seed_games


async def test_event_happy_path(client, make_user):
    games = await seed_games()
    host, host_h = await make_user()
    guest, guest_h = await make_user()
    await onboard(client, host_h, games=[games["valorant"]])
    await onboard(client, guest_h, games=[games["valorant"]])

    event = await create_event(client, host_h, games["valorant"])
    assert event["status"] == "open" and event["is_host"] and len(event["participants"]) == 1

    r = await client.post(f"/events/{event['id']}/join", headers=guest_h)
    assert r.status_code == 200 and r.json()["status"] == "full"

    third, third_h = await make_user()
    r = await client.post(f"/events/{event['id']}/join", headers=third_h)
    assert r.status_code == 409 and r.json()["code"] == "EVENT_FULL"

    r = await client.post(f"/events/{event['id']}/start", headers=guest_h)
    assert r.status_code == 403 and r.json()["code"] == "HOST_ONLY"

    assert (await client.post(f"/events/{event['id']}/start", headers=host_h)).json()["status"] == "in_progress"
    assert (await client.post(f"/events/{event['id']}/finish", headers=host_h)).json()["status"] == "finished"

    listed = await client.get("/events", headers=host_h)
    assert all(e["id"] != event["id"] for e in listed.json()), "finished events leave the default feed"
    mine = await client.get("/events?mine=true", headers=host_h)
    assert any(e["id"] == event["id"] for e in mine.json())


async def test_leave_rules(client, make_user):
    games = await seed_games()
    _, host_h = await make_user()
    _, guest_h = await make_user()
    event = await create_event(client, host_h, games["valorant"], max_slots=3)
    await client.post(f"/events/{event['id']}/join", headers=guest_h)

    r = await client.post(f"/events/{event['id']}/leave", headers=host_h)
    assert r.status_code == 409 and r.json()["code"] == "HOST_CANNOT_LEAVE"
    r = await client.post(f"/events/{event['id']}/leave", headers=guest_h)
    assert r.status_code == 200 and len(r.json()["participants"]) == 1


async def test_game_date_rules(client, make_user):
    games = await seed_games()
    _, adult_h = await make_user()
    await onboard(client, adult_h, modes=("dating",), games=[games["among-us"]])

    r = await client.post(
        "/events",
        headers=adult_h,
        json={
            "game_id": str(games["valorant"].id),
            "kind": "game_date",
            "title": "Ranked date?",
            "starts_at": "2030-01-01T20:00:00Z",
            "max_slots": 5,
        },
    )
    assert r.status_code == 422 and r.json()["code"] == "GAME_DATE_REQUIRES_CHILL_GAME"

    event = await create_event(client, adult_h, games["among-us"], kind="game_date", max_slots=5, title="Sus date")
    assert event["max_slots"] == 2, "game dates are always for two"

    _, duo_only_h = await make_user()
    await onboard(client, duo_only_h, modes=("duo",))
    feed = await client.get("/events", headers=duo_only_h)
    assert all(e["id"] != event["id"] for e in feed.json())
    r = await client.post(f"/events/{event['id']}/join", headers=duo_only_h)
    assert r.status_code == 403 and r.json()["code"] == "EVENT_NOT_VISIBLE"

    _, minor_h = await make_user(birth_date=date(date.today().year - 16, 1, 1))
    r = await client.post(
        "/events",
        headers=minor_h,
        json={
            "game_id": str(games["among-us"].id),
            "kind": "game_date",
            "title": "Nope",
            "starts_at": "2030-01-01T20:00:00Z",
        },
    )
    assert r.status_code == 422 and r.json()["code"] == "GAME_DATE_REQUIRES_DATING_MODE"
