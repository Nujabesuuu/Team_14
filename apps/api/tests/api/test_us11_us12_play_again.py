"""US-11 Таємна відповідь «Зіграємо ще?» and US-12 Метч (BR-12, BR-13, BR-14, NEVER-03).

Written from requirements and contracts. Every game here is counted by the server through finish_and_count;
the 24-hour window is then moved by rewriting counted_at. Maksym hosts, Olena joins.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update

from app.core.db import SessionLocal
from app.models import User
from app.ws.hub import hub
from tests.helpers import finish_and_count, onboard, parse_dt, seed_games, set_event_times

DATING = ("duo", "dating")
NO_DATING = ("duo",)


async def counted_game(client, make_user, *, olena_modes=DATING, maksym_modes=DATING):
    games = await seed_games()
    maksym, maksym_h = await make_user(display_name="Maksym")
    olena, olena_h = await make_user(display_name="Olena")
    await onboard(client, maksym_h, modes=maksym_modes, games=[games["overcooked-2"]])
    await onboard(client, olena_h, modes=olena_modes, games=[games["overcooked-2"]])
    event = await finish_and_count(client, maksym_h, olena_h, games["overcooked-2"])
    return event, (maksym, maksym_h), (olena, olena_h)


async def answer(client, event_id, headers, to_user_id, value):
    return await client.post(
        f"/events/{event_id}/feedback", headers=headers, json={"to_user_id": to_user_id, "answer": value}
    )


async def matches(client, headers) -> list[dict]:
    r = await client.get("/matches", headers=headers)
    assert r.status_code == 200
    return r.json()


async def counted_ago(event_id: str, elapsed: timedelta) -> None:
    """The game was counted `elapsed` ago; start and finish move with it so the timeline stays consistent."""
    counted_at = datetime.now(UTC).replace(microsecond=0) - elapsed
    await set_event_times(
        event_id, started_at=counted_at - timedelta(minutes=50), finished_at=counted_at, counted_at=counted_at
    )


# --- «Ближче» і «Побачення» -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "olena_modes,maksym_modes,allowed",
    [(DATING, DATING, True), (DATING, NO_DATING, False), (NO_DATING, DATING, False), (NO_DATING, NO_DATING, False)],
    ids=["on | on | available", "on | off | unavailable", "off | on | unavailable", "off | off | unavailable"],
)
async def test_closer_depends_on_dating_in_both(client, make_user, olena_modes, maksym_modes, allowed):
    """US-11 Scenario Outline: «Ближче» залежить від «Побачення» в обох (BR-13)."""
    event, (maksym, _), (_, olena_h) = await counted_game(
        client, make_user, olena_modes=olena_modes, maksym_modes=maksym_modes
    )

    r = await client.get(f"/events/{event['id']}/feedback", headers=olena_h)
    assert r.status_code == 200, r.text
    assert r.json()["closer_allowed"] == {maksym["id"]: allowed}

    r = await answer(client, event["id"], olena_h, maksym["id"], "closer")
    if allowed:
        assert r.status_code == 200 and r.json()["match_created"] is False
        assert maksym["id"] in (await client.get(f"/events/{event['id']}/feedback", headers=olena_h)).json()["done"]
    else:
        assert r.status_code == 422 and r.json()["code"] == "CLOSER_REQUIRES_DATING"
        state = (await client.get(f"/events/{event['id']}/feedback", headers=olena_h)).json()
        assert [p["id"] for p in state["pending"]] == [maksym["id"]] and state["done"] == []


async def test_without_dating_teammate_and_no_are_still_offered(client, make_user):
    """US-03 Scenario: Із вимкненим «Побаченням» «ближче» не пропонується — but «again» and «no» work."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user, maksym_modes=NO_DATING)

    r = await answer(client, event["id"], maksym_h, olena["id"], "again")
    assert r.status_code == 200 and r.json()["match_created"] is False
    r = await answer(client, event["id"], olena_h, maksym["id"], "no")
    assert r.status_code == 200 and r.json()["match_created"] is False
    for h, partner in ((maksym_h, olena), (olena_h, maksym)):
        assert (await client.get(f"/events/{event['id']}/feedback", headers=h)).json()["done"] == [partner["id"]]


async def test_maksym_turned_dating_off_after_olena_chose_closer(client, make_user):
    """US-12 Scenario: Максим вимкнув «Побачення» до відповіді."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    r = await answer(client, event["id"], olena_h, maksym["id"], "closer")
    assert r.status_code == 200 and r.json()["match_created"] is False

    r = await client.put("/me", headers=maksym_h, json={"modes": list(NO_DATING)})
    assert r.status_code == 200 and "dating" not in r.json()["profile"]["modes"]

    r = await client.get(f"/events/{event['id']}/feedback", headers=maksym_h)
    assert r.status_code == 200
    assert r.json()["closer_allowed"] == {olena["id"]: False}
    r = await answer(client, event["id"], maksym_h, olena["id"], "closer")
    assert r.status_code == 422 and r.json()["code"] == "CLOSER_REQUIRES_DATING"
    assert await matches(client, maksym_h) == []
    assert await matches(client, olena_h) == []


# --- 24 години -------------------------------------------------------------------------------------------


async def test_window_closes_24_hours_after_counting(client, make_user):
    """US-07 checklist 5 / US-11 checklist 2: feedback_closes_at = counted_at + 24 h."""
    event, (_, maksym_h), (_, olena_h) = await counted_game(client, make_user)
    assert parse_dt(event["feedback_closes_at"]) - parse_dt(event["counted_at"]) == timedelta(hours=24)

    await counted_ago(event["id"], timedelta(hours=5))
    for h in (maksym_h, olena_h):
        moved = (await client.get(f"/events/{event['id']}", headers=h)).json()
        assert parse_dt(moved["feedback_closes_at"]) - parse_dt(moved["counted_at"]) == timedelta(hours=24)


async def test_answer_at_23_59_is_accepted(client, make_user):
    """US-11 Scenario Outline: 24 години на відповідь — 23 h 59 min | can answer."""
    event, (maksym, _), (_, olena_h) = await counted_game(client, make_user)
    await counted_ago(event["id"], timedelta(hours=23, minutes=59))

    r = await answer(client, event["id"], olena_h, maksym["id"], "again")
    assert r.status_code == 200, r.text
    assert (await client.get(f"/events/{event['id']}/feedback", headers=olena_h)).json()["done"] == [maksym["id"]]


@pytest.mark.parametrize(
    "elapsed",
    [timedelta(hours=24), timedelta(hours=24, minutes=1)],
    ids=["exactly 24 h 0 min | too late", "24 h 1 min | too late"],
)
async def test_answer_after_24_hours_is_rejected(client, make_user, elapsed):
    """US-11 Scenario Outline: 24 години на відповідь — the time is up (checklist 3: 24 h 0 min is already late)."""
    event, (maksym, _), (_, olena_h) = await counted_game(client, make_user)
    await counted_ago(event["id"], elapsed)

    r = await answer(client, event["id"], olena_h, maksym["id"], "again")
    assert r.status_code == 409 and r.json()["code"] == "FEEDBACK_WINDOW_CLOSED"
    # The late answer was not stored. The contract gives GET /feedback no window error, so it still answers.
    r = await client.get(f"/events/{event['id']}/feedback", headers=olena_h)
    assert r.status_code == 200 and r.json()["done"] == []


async def test_no_match_when_maksym_did_not_answer_in_24_hours(client, make_user):
    """US-12 Scenario: Максим не відповів за 24 години."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    assert (await answer(client, event["id"], olena_h, maksym["id"], "closer")).status_code == 200
    await counted_ago(event["id"], timedelta(hours=24, minutes=1))

    r = await answer(client, event["id"], maksym_h, olena["id"], "closer")
    assert r.status_code == 409 and r.json()["code"] == "FEEDBACK_WINDOW_CLOSED"
    assert await matches(client, maksym_h) == []
    assert await matches(client, olena_h) == []


# --- Комбінації відповідей і метч ------------------------------------------------------------------------


async def test_mutual_closer_creates_match_and_opens_chat(client, make_user):
    """US-12 Scenario Outline: Метч за комбінацією відповідей — closer | closer | match (Scenario: Взаємне «ближче»)."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)

    r = await answer(client, event["id"], olena_h, maksym["id"], "closer")
    assert r.status_code == 200 and r.json() == {"match_created": False, "match_id": None}
    r = await answer(client, event["id"], maksym_h, olena["id"], "closer")
    assert r.status_code == 200 and r.json()["match_created"] is True
    match_id = r.json()["match_id"]

    for h, other in ((olena_h, maksym), (maksym_h, olena)):
        mine = await matches(client, h)
        assert [(m["id"], m["other"]["id"], m["source"]) for m in mine] == [(match_id, other["id"], "post_game")]
        chat = await client.get(f"/conversations/{mine[0]['conversation_id']}/messages", headers=h)
        assert chat.status_code == 200 and chat.json() == []


@pytest.mark.parametrize("maksym_answer", ["again", "no"], ids=["closer | again | no match", "closer | no | no match"])
async def test_closer_with_any_other_answer_is_not_a_match(client, make_user, maksym_answer):
    """US-12 Scenario Outline: Метч за комбінацією відповідей (BR-14)."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    assert (await answer(client, event["id"], olena_h, maksym["id"], "closer")).status_code == 200

    r = await answer(client, event["id"], maksym_h, olena["id"], maksym_answer)
    assert r.status_code == 200 and r.json() == {"match_created": False, "match_id": None}
    assert await matches(client, olena_h) == []
    assert await matches(client, maksym_h) == []


# --- Таємність (NEVER-03) --------------------------------------------------------------------------------


def string_values(value) -> list[str]:
    if isinstance(value, dict):
        return [s for v in value.values() for s in string_values(v)]
    if isinstance(value, list):
        return [s for v in value for s in string_values(v)]
    return [value] if isinstance(value, str) else []


@pytest.mark.parametrize(
    "secret",
    ["closer", "no"],
    ids=["Olena chose closer | Maksym sees nothing", "Olena chose no | Maksym sees nothing"],
)
async def test_one_sided_answer_is_invisible_to_the_partner(client, make_user, secret):
    """US-11 «Олена обирає «ближче»», «Відповідь «ні» невидима»; US-12 «Односторонній вибір не видно»; NEVER-03."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    feedback_before = (await client.get(f"/events/{event['id']}/feedback", headers=maksym_h)).json()
    event_before = (await client.get(f"/events/{event['id']}", headers=maksym_h)).json()

    r = await answer(client, event["id"], olena_h, maksym["id"], secret)
    assert r.status_code == 200 and r.json()["match_created"] is False
    assert (await client.get(f"/events/{event['id']}/feedback", headers=olena_h)).json()["done"] == [maksym["id"]]

    feedback_after = (await client.get(f"/events/{event['id']}/feedback", headers=maksym_h)).json()
    assert feedback_after == feedback_before, "nothing in Maksym's view may change after Olena's answer"
    assert [p["id"] for p in feedback_after["pending"]] == [olena["id"]] and feedback_after["done"] == []
    assert secret not in string_values(feedback_after)
    assert (await client.get(f"/events/{event['id']}", headers=maksym_h)).json() == event_before
    assert await matches(client, maksym_h) == []


# --- Found by the independent audit (prompt 6.3). ---


async def test_block_after_the_game_removes_the_teammate_and_prevents_a_match(client, make_user):
    """BR-21 + US-12: Maksym said "closer", then Olena blocked him. He must vanish from her questions, and her
    "closer" must not create a match — answered exactly like "no match", so he learns nothing (NEVER-05)."""
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    assert (await answer(client, event["id"], maksym_h, olena["id"], "closer")).status_code == 200
    assert (await client.post("/blocks", headers=olena_h, json={"user_id": maksym["id"]})).status_code == 204

    pending = (await client.get(f"/events/{event['id']}/feedback", headers=olena_h)).json()
    assert pending["pending"] == [] and pending["closer_allowed"] == {}
    r = await answer(client, event["id"], olena_h, maksym["id"], "closer")
    assert r.status_code == 200 and r.json() == {"match_created": False, "match_id": None}
    assert await matches(client, maksym_h) == [] and await matches(client, olena_h) == []


async def test_the_blocked_one_cannot_get_a_match_either(client, make_user):
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    assert (await answer(client, event["id"], olena_h, maksym["id"], "closer")).status_code == 200
    assert (await client.post("/blocks", headers=olena_h, json={"user_id": maksym["id"]})).status_code == 204
    # He played with her, so a distinct error would tell him he is blocked (NEVER-05): it looks like "no match yet".
    r = await answer(client, event["id"], maksym_h, olena["id"], "closer")
    assert r.status_code == 200 and r.json() == {"match_created": False, "match_id": None}
    assert await matches(client, maksym_h) == []


async def test_answer_about_a_banned_teammate_changes_nothing(client, make_user):
    """A banned account is gone from the questions (US-10); a stale answer about it changes nothing."""
    event, (maksym, _), (_, olena_h) = await counted_game(client, make_user)
    async with SessionLocal() as s:
        await s.execute(update(User).where(User.id == uuid.UUID(maksym["id"])).values(banned_at=datetime.now(UTC)))
        await s.commit()
    r = await answer(client, event["id"], olena_h, maksym["id"], "closer")
    assert r.status_code == 200 and r.json() == {"match_created": False, "match_id": None}
    assert await matches(client, olena_h) == []


async def test_mutual_closer_sent_at_the_same_moment_makes_exactly_one_match(client, make_user):
    event, (maksym, maksym_h), (olena, olena_h) = await counted_game(client, make_user)
    r1, r2 = await asyncio.gather(
        answer(client, event["id"], maksym_h, olena["id"], "closer"),
        answer(client, event["id"], olena_h, maksym["id"], "closer"),
    )
    assert r1.status_code == 200 and r2.status_code == 200, (r1.text, r2.text)
    assert len(await matches(client, maksym_h)) == 1 and len(await matches(client, olena_h)) == 1


async def test_one_sided_closer_sends_nothing_over_websocket(client, make_user, monkeypatch):
    """«Односторонній вибір не видно … не отримує жодного повідомлення» (NEVER-03): not even a WS event."""
    event, (maksym, maksym_h), (olena, _) = await counted_game(client, make_user)
    sent: list[str] = []

    async def capture(user_id, payload):
        sent.append(str(user_id))

    monkeypatch.setattr(hub, "send_to_user", capture)
    assert (await answer(client, event["id"], maksym_h, olena["id"], "closer")).status_code == 200
    assert olena["id"] not in sent
