"""US-07. Підтвердження гри (BR-09, BR-10, BR-11). Written from requirements and contracts.

Durations are set by rewriting started_at / finished_at in the database (set_event_times); the server
compares them with its real clock. Maksym hosts, Olena joins.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.ws.hub import hub
from tests.helpers import create_event, parse_dt, play_together, seed_games, set_event_times


async def play(client, make_user, played: timedelta):
    """Maksym and Olena play Overcooked 2 for `played`, the game ended five minutes ago. Nobody has confirmed yet."""
    games = await seed_games()
    maksym, maksym_h = await make_user(display_name="Maksym")
    olena, olena_h = await make_user(display_name="Olena")
    event = await play_together(client, maksym_h, olena_h, games["overcooked-2"])
    finished_at = datetime.now(UTC).replace(microsecond=0) - timedelta(minutes=5)
    await set_event_times(event["id"], started_at=finished_at - played, finished_at=finished_at)
    return event, (maksym, maksym_h), (olena, olena_h)


async def confirm(client, event_id, headers):
    return await client.post(f"/events/{event_id}/confirm", headers=headers)


@pytest.mark.parametrize(
    "played,who,counted",
    [
        (timedelta(minutes=15), "both", True),
        (timedelta(minutes=45), "both", True),
        (timedelta(minutes=14, seconds=59), "both", False),
        (timedelta(minutes=10), "both", False),
        (timedelta(minutes=45), "only Olena", False),
    ],
    ids=[
        "15 min | both | counted",
        "45 min | both | counted",
        "14 min 59 s | both | not counted",
        "10 min | both | not counted",
        "45 min | only Olena | not counted",
    ],
)
async def test_game_counting_rule(client, make_user, played, who, counted):
    """US-07 Scenario Outline: Правило зарахування гри (BR-11)."""
    event, (_, maksym_h), (_, olena_h) = await play(client, make_user, played)
    confirmers = [olena_h, maksym_h] if who == "both" else [olena_h]

    for n, h in enumerate(confirmers, start=1):
        r = await confirm(client, event["id"], h)
        assert r.status_code == 200, r.text
        assert r.json()["confirmations"] == n and r.json()["confirmed_by_me"] is True
    # The answer to the last confirmation already says whether the game counted: the lobby and the WS update are
    # built from it, and a later GET must not be the only place where "Play again?" appears (mutation check, 6.3).
    assert (r.json()["counted_at"] is not None) is counted

    r = await client.get(f"/events/{event['id']}", headers=olena_h)
    assert r.status_code == 200
    after = r.json()
    assert after["status"] == "finished"
    assert after["confirmations"] == len(confirmers)
    assert (after["counted_at"] is not None) is counted
    if counted:
        assert after["feedback_closes_at"] is not None
    else:
        assert after["feedback_closes_at"] is None


async def test_confirmation_is_personal(client, make_user):
    """US-07 contract: confirmed_by_me reflects only my own confirmation."""
    event, (_, maksym_h), (_, olena_h) = await play(client, make_user, timedelta(minutes=45))
    assert (await confirm(client, event["id"], olena_h)).status_code == 200

    as_maksym = (await client.get(f"/events/{event['id']}", headers=maksym_h)).json()
    assert as_maksym["confirmations"] == 1 and as_maksym["confirmed_by_me"] is False
    assert as_maksym["counted_at"] is None, "one confirmation never counts a game"


async def test_counted_game_opens_play_again_for_both(client, make_user):
    """US-07 Scenario: Зарахована гра відкриває «Зіграємо ще?»."""
    event, (maksym, maksym_h), (olena, olena_h) = await play(client, make_user, timedelta(minutes=45))
    for h in (olena_h, maksym_h):
        assert (await confirm(client, event["id"], h)).status_code == 200

    for h, partner in ((olena_h, maksym), (maksym_h, olena)):
        r = await client.get(f"/events/{event['id']}/feedback", headers=h)
        assert r.status_code == 200, r.text
        assert [p["id"] for p in r.json()["pending"]] == [partner["id"]]


async def test_short_game_does_not_open_play_again(client, make_user):
    """US-07 Scenario: Короткий івент не відкриває «Зіграємо ще?» — 10 minutes, both confirmed."""
    event, (maksym, maksym_h), (_, olena_h) = await play(client, make_user, timedelta(minutes=10))
    for h in (olena_h, maksym_h):
        assert (await confirm(client, event["id"], h)).status_code == 200

    r = await client.get(f"/events/{event['id']}/feedback", headers=olena_h)
    assert r.status_code == 409 and r.json()["code"] == "GAME_NOT_COUNTED"
    r = await client.post(
        f"/events/{event['id']}/feedback", headers=olena_h, json={"to_user_id": maksym["id"], "answer": "again"}
    )
    assert r.status_code == 409 and r.json()["code"] == "GAME_NOT_COUNTED"


async def test_single_confirmation_does_not_open_play_again(client, make_user):
    """US-07 checklist 2 and 6: 45 minutes but only Olena confirmed — no «Зіграємо ще?»."""
    event, _, (_, olena_h) = await play(client, make_user, timedelta(minutes=45))
    assert (await confirm(client, event["id"], olena_h)).status_code == 200

    r = await client.get(f"/events/{event['id']}/feedback", headers=olena_h)
    assert r.status_code == 409 and r.json()["code"] == "GAME_NOT_COUNTED"


async def test_outsider_cannot_confirm(client, make_user):
    """US-07 contract: only a participant confirms the game (403 NOT_PARTICIPANT)."""
    event, _, (_, olena_h) = await play(client, make_user, timedelta(minutes=45))
    _, darina_h = await make_user(display_name="Darina")

    r = await confirm(client, event["id"], darina_h)
    assert r.status_code == 403 and r.json()["code"] == "NOT_PARTICIPANT"
    after = (await client.get(f"/events/{event['id']}", headers=olena_h)).json()
    assert after["confirmations"] == 0


@pytest.mark.parametrize("stage", ["open", "in_progress"], ids=["before start", "while playing"])
async def test_cannot_confirm_before_the_game_is_finished(client, make_user, stage):
    """US-07 contract: confirming an unfinished event gives 409 EVENT_NOT_FINISHED."""
    games = await seed_games()
    _, maksym_h = await make_user(display_name="Maksym")
    _, olena_h = await make_user(display_name="Olena")
    event = await create_event(client, maksym_h, games["overcooked-2"])
    assert (await client.post(f"/events/{event['id']}/join", headers=olena_h)).status_code == 200
    if stage == "in_progress":
        assert (await client.post(f"/events/{event['id']}/start", headers=maksym_h)).status_code == 200

    r = await confirm(client, event["id"], olena_h)
    assert r.status_code == 409 and r.json()["code"] == "EVENT_NOT_FINISHED"
    after = (await client.get(f"/events/{event['id']}", headers=olena_h)).json()
    assert after["confirmations"] == 0 and after["confirmed_by_me"] is False


async def test_second_confirmation_by_same_person_is_rejected(client, make_user):
    """US-07 contract: one person confirms once (409 ALREADY_CONFIRMED); the host alone never counts a game."""
    event, (_, maksym_h), _ = await play(client, make_user, timedelta(minutes=45))
    assert (await confirm(client, event["id"], maksym_h)).status_code == 200

    r = await confirm(client, event["id"], maksym_h)
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_CONFIRMED"
    after = (await client.get(f"/events/{event['id']}", headers=maksym_h)).json()
    assert after["confirmations"] == 1 and after["counted_at"] is None


async def start_and_forget(client, make_user, since_start: timedelta):
    """Taras starts the event and never presses «Finish»; `since_start` has passed."""
    games = await seed_games()
    _, taras_h = await make_user(display_name="Taras")
    _, olena_h = await make_user(display_name="Olena")
    event = await create_event(client, taras_h, games["overcooked-2"])
    assert (await client.post(f"/events/{event['id']}/join", headers=olena_h)).status_code == 200
    assert (await client.post(f"/events/{event['id']}/start", headers=taras_h)).status_code == 200
    started_at = datetime.now(UTC).replace(microsecond=0) - since_start
    await set_event_times(event["id"], started_at=started_at)
    return event, started_at, taras_h, olena_h


async def test_event_finishes_itself_three_hours_after_start(client, make_user):
    """US-07 Scenario: Івент завершується сам, якщо хост забув (BR-10)."""
    event, started_at, taras_h, olena_h = await start_and_forget(client, make_user, timedelta(hours=3))

    r = await client.get(f"/events/{event['id']}", headers=olena_h)
    assert r.status_code == 200
    after = r.json()
    assert after["status"] == "finished"
    assert after["finished_at"] is not None
    assert abs(parse_dt(after["finished_at"]) - (started_at + timedelta(hours=3))) < timedelta(seconds=1)

    for n, h in enumerate((olena_h, taras_h), start=1):
        r = await confirm(client, event["id"], h)
        assert r.status_code == 200, r.text
        assert r.json()["confirmations"] == n
    assert (await client.get(f"/events/{event['id']}", headers=olena_h)).json()["counted_at"] is not None


async def test_event_is_still_running_just_before_three_hours(client, make_user):
    """US-07 checklist 4, boundary: at 2 h 59 min the event is still in progress and cannot be confirmed."""
    event, _, _, olena_h = await start_and_forget(client, make_user, timedelta(hours=2, minutes=59))

    after = (await client.get(f"/events/{event['id']}", headers=olena_h)).json()
    assert after["status"] == "in_progress" and after["finished_at"] is None
    r = await confirm(client, event["id"], olena_h)
    assert r.status_code == 409 and r.json()["code"] == "EVENT_NOT_FINISHED"


# --- Found by the independent audit (prompt 6.3): concurrency and realtime paths the first tests did not touch. ---


async def test_both_confirming_at_the_same_moment_still_counts_the_game(client, make_user):
    """US-07 «Правило зарахування», 45 хв, обоє — but both press "confirm" at once.

    Each request used to count only the confirmation it had added itself, so neither counted the game, and a
    second press is ALREADY_CONFIRMED: "Play again?" would never open for this pair.
    """
    event, (_, maksym_h), (_, olena_h) = await play(client, make_user, timedelta(minutes=45))
    r1, r2 = await asyncio.gather(confirm(client, event["id"], maksym_h), confirm(client, event["id"], olena_h))
    assert r1.status_code == 200 and r2.status_code == 200
    after = (await client.get(f"/events/{event['id']}", headers=olena_h)).json()
    assert after["confirmations"] == 2
    assert after["counted_at"] is not None
    r = await client.get(f"/events/{event['id']}/feedback", headers=olena_h)
    assert r.status_code == 200


async def test_double_click_on_confirm_is_a_conflict_not_a_server_error(client, make_user):
    event, (_, maksym_h), _ = await play(client, make_user, timedelta(minutes=45))
    r1, r2 = await asyncio.gather(confirm(client, event["id"], maksym_h), confirm(client, event["id"], maksym_h))
    assert sorted(r.status_code for r in (r1, r2)) == [200, 409]
    loser = r1 if r1.status_code == 409 else r2
    assert loser.json()["code"] == "ALREADY_CONFIRMED"


async def test_auto_finish_seen_in_the_feed_tells_the_other_participant(client, make_user, monkeypatch):
    """US-07 «Івент завершується сам»: whoever opens the app first finishes it, and the open lobby of the
    other participant learns about it over WS (contract: event.updated), so the confirm button appears there."""
    games = await seed_games()
    maksym, maksym_h = await make_user(display_name="Maksym")
    olena, olena_h = await make_user(display_name="Olena")
    event = await create_event(client, maksym_h, games["overcooked-2"])
    await client.post(f"/events/{event['id']}/join", headers=olena_h)
    await client.post(f"/events/{event['id']}/start", headers=maksym_h)
    await set_event_times(event["id"], started_at=datetime.now(UTC) - timedelta(hours=3, minutes=1))

    sent: list[tuple[str, dict]] = []

    async def capture(user_id, payload):
        sent.append((str(user_id), payload))

    monkeypatch.setattr(hub, "send_to_user", capture)
    feed = (await client.get("/events?mine=true", headers=olena_h)).json()
    assert next(e for e in feed if e["id"] == event["id"])["status"] == "finished"
    to_maksym = [p for uid, p in sent if uid == maksym["id"] and p["type"] == "event.updated"]
    assert to_maksym and to_maksym[-1]["event"]["status"] == "finished"
