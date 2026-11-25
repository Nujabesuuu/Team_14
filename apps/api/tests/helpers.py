"""Shared helpers for API tests: seed games and drive the event flow through the public API."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models import Event, Game, User, UserRole

GAMES = {
    "valorant": ("Valorant", False),
    "dota2": ("Dota 2", False),
    "among-us": ("Among Us", True),
    "overcooked-2": ("Overcooked 2", True),
}


async def seed_games() -> dict[str, Game]:
    async with SessionLocal() as s:
        out = {}
        for slug, (name, chill) in GAMES.items():
            g = Game(name=name, slug=slug, is_chill=chill)
            s.add(g)
            out[slug] = g
        await s.commit()
        for g in out.values():
            await s.refresh(g)
        return out


async def onboard(client, headers, *, modes=("duo",), games=(), role="support", **extra) -> None:
    payload = {
        "modes": list(modes),
        "role": role,
        "playstyle": "casual",
        "comms": "voice",
        "schedule": ["evening"],
        "toxicity_tolerance": 3,
        "games": [{"game_id": str(g.id)} for g in games],
        **extra,
    }
    r = await client.put("/me", headers=headers, json=payload)
    assert r.status_code == 200, r.text


async def create_event(client, headers, game, *, kind="squad", max_slots=2, title="Duo tonight") -> dict:
    r = await client.post(
        "/events",
        headers=headers,
        json={
            "game_id": str(game.id),
            "kind": kind,
            "title": title,
            "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
            "max_slots": max_slots,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def play_together(client, host_h, guest_h, game) -> dict:
    """Host creates, guest joins, host starts and finishes. Returns the finished event, not yet counted (US-07)."""
    event = await create_event(client, host_h, game)
    r = await client.post(f"/events/{event['id']}/join", headers=guest_h)
    assert r.status_code == 200, r.text
    assert (await client.post(f"/events/{event['id']}/start", headers=host_h)).status_code == 200
    r = await client.post(f"/events/{event['id']}/finish", headers=host_h)
    assert r.status_code == 200, r.text
    return r.json()


async def enable_dating(client, headers) -> None:
    """Adds Dating to the person's modes, keeping the others: "closer" needs Dating on both sides (US-11)."""
    modes = (await client.get("/me", headers=headers)).json()["profile"]["modes"]
    if "dating" not in modes:
        r = await client.put("/me", headers=headers, json={"modes": [*modes, "dating"]})
        assert r.status_code == 200, r.text


async def match_via_feedback(client, event_id, a_h, a_id, b_h, b_id) -> str:
    """Both answer "closer" after a counted game. Turns Dating on for both first, as the rule requires."""
    for h in (a_h, b_h):
        await enable_dating(client, h)
    r = await client.post(f"/events/{event_id}/feedback", headers=a_h, json={"to_user_id": b_id, "answer": "closer"})
    assert r.status_code == 200 and r.json()["match_created"] is False
    r = await client.post(f"/events/{event_id}/feedback", headers=b_h, json={"to_user_id": a_id, "answer": "closer"})
    assert r.status_code == 200 and r.json()["match_created"] is True, r.text
    return r.json()["match_id"]


async def make_moderator(user_id: str) -> None:
    """Moderators are appointed by the team (seed), never through the API, so tests write the role directly."""
    async with SessionLocal() as s:
        user = await s.get(User, uuid.UUID(user_id))
        user.role = UserRole.moderator
        await s.commit()


async def set_birth_date(user_id: str, birth_date) -> None:
    """Registration refuses minors (US-01), so an under-18 account exists only in the DB: created before G-01 was
    fixed, or with a corrected birth date. Tests use it to check the second line of defence (Dating, Game Date)."""
    async with SessionLocal() as s:
        user = await s.get(User, uuid.UUID(user_id))
        user.birth_date = birth_date
        await s.commit()


def parse_dt(value: str) -> datetime:
    """ISO 8601 from the API as an aware UTC datetime. A missing offset is read as UTC: that is gap G-10, not US-07."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


async def set_event_times(
    event_id: str,
    *,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    counted_at: datetime | None = None,
) -> None:
    """Moves an event in time. The app clock is never faked, so tests shift the stored moments instead.

    A plain UPDATE (not setattr) so a column missing from the model fails loudly instead of being ignored.
    """
    values = {
        k: v
        for k, v in {"started_at": started_at, "finished_at": finished_at, "counted_at": counted_at}.items()
        if v is not None
    }
    assert values, "nothing to set"
    async with SessionLocal() as s:
        await s.execute(update(Event).where(Event.id == uuid.UUID(event_id)).values(**values))
        await s.commit()


async def finish_and_count(client, host_h, guest_h, game) -> dict:
    """Play a 45-minute game and have both confirm it, so the server counts it by the rule (US-07, BR-11).

    The duration is written before the confirmations: the server decides on `counted_at` when the second
    confirmation arrives, and must see a game of at least 15 minutes at that moment. `counted_at` itself
    is never written here. Returns the event as the host sees it afterwards.
    """
    event = await play_together(client, host_h, guest_h, game)
    now = datetime.now(UTC)
    await set_event_times(event["id"], started_at=now - timedelta(minutes=50), finished_at=now - timedelta(minutes=5))
    for h in (host_h, guest_h):
        r = await client.post(f"/events/{event['id']}/confirm", headers=h)
        assert r.status_code == 200, r.text
    r = await client.get(f"/events/{event['id']}", headers=host_h)
    assert r.status_code == 200, r.text
    counted = r.json()
    assert counted["counted_at"] is not None, "a 45-minute game confirmed by both must be counted"
    return counted
