"""Shared helpers for API tests: seed games and drive the event flow through the public API."""

from datetime import UTC, datetime, timedelta

from app.core.db import SessionLocal
from app.models import Game

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
    """Host creates, guest joins, host starts and finishes. Returns the finished event."""
    event = await create_event(client, host_h, game)
    r = await client.post(f"/events/{event['id']}/join", headers=guest_h)
    assert r.status_code == 200, r.text
    assert (await client.post(f"/events/{event['id']}/start", headers=host_h)).status_code == 200
    r = await client.post(f"/events/{event['id']}/finish", headers=host_h)
    assert r.status_code == 200, r.text
    return r.json()


async def match_via_feedback(client, event_id, a_h, a_id, b_h, b_id) -> str:
    r = await client.post(f"/events/{event_id}/feedback", headers=a_h, json={"to_user_id": b_id, "answer": "closer"})
    assert r.status_code == 200 and r.json()["match_created"] is False
    r = await client.post(f"/events/{event_id}/feedback", headers=b_h, json={"to_user_id": a_id, "answer": "closer"})
    assert r.status_code == 200 and r.json()["match_created"] is True, r.text
    return r.json()["match_id"]
