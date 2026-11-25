"""US-19. Створення івенту (BR-06, BR-07, BR-21, NEVER-05). Written from requirements and contracts."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from tests.helpers import onboard, parse_dt, seed_games


def payload(game, **overrides) -> dict:
    body = {
        "game_id": str(game.id),
        "kind": "squad",
        "title": "Overcooked 2 for four",
        "starts_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        "max_slots": 4,
    }
    return {**body, **overrides}


async def my_events(client, headers) -> list[dict]:
    r = await client.get("/events?mine=true", headers=headers)
    assert r.status_code == 200
    return r.json()


async def feed_ids(client, headers) -> list[str]:
    r = await client.get("/events", headers=headers)
    assert r.status_code == 200
    return [e["id"] for e in r.json()]


@pytest.fixture
async def taras(client, make_user):
    games = await seed_games()
    user, headers = await make_user(display_name="Taras")
    await onboard(client, headers, games=[games["overcooked-2"]])
    return user, headers, games


async def test_host_creates_event_and_others_see_it(client, make_user, taras):
    """US-19 Scenario: Тарас створює івент на вечір."""
    host, host_h, games = taras
    _, olena_h = await make_user(display_name="Olena")
    await onboard(client, olena_h, games=[games["overcooked-2"]])

    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"]))
    assert r.status_code == 201, r.text
    event = r.json()
    assert event["is_host"] is True and event["is_participant"] is True
    assert [p["id"] for p in event["participants"]] == [host["id"]], "the host is the first participant (BR-07)"
    assert event["status"] == "open" and event["max_slots"] == 4

    mine = await my_events(client, host_h)
    assert [(e["id"], e["is_host"]) for e in mine] == [(event["id"], True)]

    r = await client.get("/events", headers=olena_h)
    assert r.status_code == 200
    seen = [e for e in r.json() if e["id"] == event["id"]]
    assert len(seen) == 1, "Olena sees the new event in her feed"
    assert seen[0]["is_host"] is False and seen[0]["is_participant"] is False


@pytest.mark.parametrize("slots", [2, 10], ids=["2 slots | created", "10 slots | created"])
async def test_slots_within_range_are_accepted(client, taras, slots):
    """US-19 Scenario Outline: Кількість місць — accepted rows (BR-06)."""
    _, host_h, games = taras
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], max_slots=slots))
    assert r.status_code == 201, r.text
    assert r.json()["max_slots"] == slots
    assert [e["max_slots"] for e in await my_events(client, host_h)] == [slots]


@pytest.mark.parametrize("slots", [1, 11], ids=["1 slot | 2 to 10, not created", "11 slots | 2 to 10, not created"])
async def test_slots_out_of_range_are_rejected(client, taras, slots):
    """US-19 Scenario Outline: Кількість місць — rejected rows (BR-06). Rejected, never silently clamped."""
    _, host_h, games = taras
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], max_slots=slots))
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR", r.text
    assert any("max_slots" in f["field"] for f in r.json()["fields"])
    assert await my_events(client, host_h) == []


@pytest.mark.parametrize("length", [3, 80], ids=["3 chars | created", "80 chars | created"])
async def test_title_length_within_range_is_accepted(client, taras, length):
    """US-19 checklist 1: title from 3 to 80 characters (BR-06)."""
    _, host_h, games = taras
    title = "x" * length
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], title=title))
    assert r.status_code == 201, r.text
    assert [e["title"] for e in await my_events(client, host_h)] == [title]


@pytest.mark.parametrize("length", [2, 81], ids=["2 chars | not created", "81 chars | not created"])
async def test_title_length_out_of_range_is_rejected(client, taras, length):
    """US-19 checklist 1: title from 3 to 80 characters (BR-06)."""
    _, host_h, games = taras
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], title="x" * length))
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR", r.text
    assert any("title" in f["field"] for f in r.json()["fields"])
    assert await my_events(client, host_h) == []


async def test_start_time_in_the_past_is_rejected(client, taras):
    """US-19 Scenario: Час початку в минулому — at 21:00 Taras picks 20:00 today."""
    _, host_h, games = taras
    an_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], starts_at=an_hour_ago))
    assert r.status_code == 422 and r.json()["code"] == "STARTS_IN_PAST", r.text
    assert await my_events(client, host_h) == []


async def test_start_time_a_minute_ago_is_rejected(client, taras):
    """US-19 checklist 3: any moment in the past is rejected, not only whole hours."""
    _, host_h, games = taras
    a_minute_ago = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], starts_at=a_minute_ago))
    assert r.status_code == 422 and r.json()["code"] == "STARTS_IN_PAST", r.text
    assert await my_events(client, host_h) == []


async def test_start_time_in_a_few_minutes_is_accepted(client, taras):
    """US-19 checklist 3: the near future is fine — the rule bans only the past."""
    _, host_h, games = taras
    soon = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"], starts_at=soon))
    assert r.status_code == 201, r.text


async def test_blocked_player_does_not_see_new_event(client, make_user, taras):
    """US-19 Scenario: Заблокований не бачить нового івенту (BR-21)."""
    _, host_h, games = taras
    maksym, maksym_h = await make_user(display_name="Maksym")
    _, olena_h = await make_user(display_name="Olena")
    for h in (maksym_h, olena_h):
        await onboard(client, h, games=[games["overcooked-2"]])
    assert (await client.post("/blocks", headers=host_h, json={"user_id": maksym["id"]})).status_code == 204

    r = await client.post("/events", headers=host_h, json=payload(games["overcooked-2"]))
    assert r.status_code == 201
    event_id = r.json()["id"]

    assert event_id not in await feed_ids(client, maksym_h)
    assert event_id in await feed_ids(client, olena_h), "control: the event is in the feed for everyone else"


async def test_blocked_player_cannot_join_and_learns_no_reason(client, make_user, taras):
    """US-19 checklist 5 + NEVER-05: a direct join by the blocked player gets «event not visible», not «blocked»."""
    _, host_h, games = taras
    maksym, maksym_h = await make_user(display_name="Maksym")
    await onboard(client, maksym_h, games=[games["overcooked-2"]])
    assert (await client.post("/blocks", headers=host_h, json={"user_id": maksym["id"]})).status_code == 204
    event_id = (await client.post("/events", headers=host_h, json=payload(games["overcooked-2"]))).json()["id"]

    r = await client.post(f"/events/{event_id}/join", headers=maksym_h)
    assert r.status_code == 403 and r.json()["code"] == "EVENT_NOT_VISIBLE"
    participants = (await client.get(f"/events/{event_id}", headers=host_h)).json()["participants"]
    assert maksym["id"] not in [p["id"] for p in participants]


@pytest.mark.parametrize(
    "starts_at,expected",
    [
        ("2020-01-01T20:00:00", 422),  # no zone: read as UTC, and in the past
        ("2020-01-01T20:00:00+05:00", 422),
        (None, 201),  # tomorrow, sent with +05:00
    ],
    ids=["naive past | rejected", "+05:00 past | rejected", "+05:00 tomorrow | stored in UTC"],
)
async def test_start_time_with_or_without_a_zone(client, make_user, starts_at, expected):
    """Contract: a start time without a zone is UTC; any offset is converted (found missing by the audit, 6.3)."""
    games = await seed_games()
    _, h = await make_user()
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).astimezone(timezone(timedelta(hours=5))).replace(microsecond=0)
    r = await client.post(
        "/events",
        headers=h,
        json={
            "game_id": str(games["overcooked-2"].id),
            "title": "Zones",
            "starts_at": starts_at or tomorrow.isoformat(),
            "max_slots": 2,
        },
    )
    assert r.status_code == expected, r.text
    if expected == 422:
        assert r.json()["code"] == "STARTS_IN_PAST"
    else:
        assert r.json()["starts_at"].endswith("Z")
        assert parse_dt(r.json()["starts_at"]) == tomorrow
