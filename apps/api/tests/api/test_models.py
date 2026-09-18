import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import Event, EventParticipant, Game, Profile, User, canonical_pair


async def test_models_roundtrip():
    async with SessionLocal() as s:
        user = User(email="a@b.c", password_hash="x", display_name="A", birth_date=date(2000, 1, 1))
        user.profile = Profile(modes=["duo"])
        game = Game(name="Valorant", slug="valorant")
        s.add_all([user, game])
        await s.flush()
        event = Event(host_id=user.id, game_id=game.id, title="Duo", starts_at=datetime.now(UTC))
        event.participants.append(EventParticipant(user_id=user.id))
        s.add(event)
        await s.commit()

    async with SessionLocal() as s:
        ev = (await s.execute(select(Event))).scalar_one()
        assert ev.game.slug == "valorant"
        assert ev.participant_ids == [ev.host_id]
        assert ev.host.profile.modes == ["duo"]


def test_canonical_pair_is_order_independent():
    a, b = uuid.uuid4(), uuid.uuid4()
    assert canonical_pair(a, b) == canonical_pair(b, a)
