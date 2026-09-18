"""Demo seed: `python -m app.seed`. Idempotent — skips if demo users already exist."""

import asyncio
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.core.db import SessionLocal, create_all
from app.core.security import hash_password
from app.models import (
    AvatarKey,
    Event,
    EventKind,
    EventParticipant,
    EventStatus,
    Game,
    MatchSource,
    Message,
    Profile,
    ProfileGame,
    User,
)
from app.services.matches import create_match

PASSWORD = "demo1234"

GAMES = [
    ("Valorant", "valorant", False, "#FF4655"),
    ("Dota 2", "dota2", False, "#B4432D"),
    ("League of Legends", "lol", False, "#C89B3C"),
    ("CS2", "cs2", False, "#DE9B35"),
    ("Apex Legends", "apex", False, "#DA292A"),
    ("Rocket League", "rocket-league", False, "#0077FF"),
    ("Minecraft", "minecraft", True, "#5B8731"),
    ("Among Us", "among-us", True, "#C51111"),
    ("Overcooked 2", "overcooked-2", True, "#F7A823"),
    ("GeoGuessr", "geoguessr", True, "#3A9D5D"),
    ("It Takes Two", "it-takes-two", True, "#E4572E"),
    ("Stardew Valley", "stardew-valley", True, "#7CB342"),
]

# (display_name, birth_year, avatar, accent, modes, role, playstyle, comms, schedule, toxicity, games, bio)
USERS = [
    (
        "Nika",
        2001,
        "kitsune",
        "#E60012",
        ["duo", "dating"],
        "support",
        "casual",
        "voice",
        ["evening", "weekend"],
        2,
        ["valorant", "among-us", "stardew-valley"],
        "Sage main. I will heal you and roast you in the same breath.",
    ),
    (
        "Danylo",
        1999,
        "raven",
        "#1E90FF",
        ["duo", "friends", "dating"],
        "carry",
        "competitive",
        "voice",
        ["evening", "night"],
        3,
        ["valorant", "cs2", "apex"],
        "Immortal grinder. Looking for a duo that doesn't tilt.",
    ),
    (
        "Olesia",
        2002,
        "vesper",
        "#9B59B6",
        ["friends", "dating"],
        "flex",
        "casual",
        "text",
        ["weekend", "morning"],
        1,
        ["minecraft", "stardew-valley", "it-takes-two"],
        "Cozy games only. I build farms, not KDA.",
    ),
    (
        "Taras",
        1998,
        "sentinel",
        "#2ECC71",
        ["duo"],
        "tank",
        "competitive",
        "both",
        ["evening"],
        4,
        ["dota2", "lol"],
        "Offlaner. Will absorb damage and blame.",
    ),
    (
        "Marta",
        2000,
        "oracle",
        "#F5C518",
        ["friends", "dating"],
        "igl",
        "competitive",
        "voice",
        ["night", "weekend"],
        3,
        ["cs2", "valorant", "geoguessr"],
        "I call the strats. You follow. Then we get coffee.",
    ),
    (
        "Yehor",
        2003,
        "jester",
        "#FF6B35",
        ["duo", "friends"],
        "flex",
        "casual",
        "text",
        ["night"],
        5,
        ["rocket-league", "among-us", "minecraft"],
        "Chaos agent. Sus by default.",
    ),
    (
        "Sofia",
        2001,
        "marionette",
        "#E91E63",
        ["dating"],
        "support",
        "casual",
        "both",
        ["evening", "weekend"],
        2,
        ["overcooked-2", "it-takes-two", "among-us"],
        "If we survive Overcooked together, we can survive anything.",
    ),
    (
        "Bohdan",
        1997,
        "nomad",
        "#00BCD4",
        ["duo", "dating"],
        "carry",
        "competitive",
        "voice",
        ["morning", "evening"],
        3,
        ["apex", "valorant", "rocket-league"],
        "Early bird predator. Coffee, ranked, repeat.",
    ),
    (
        "Ira",
        2002,
        "kitsune",
        "#8BC34A",
        ["friends"],
        "flex",
        "casual",
        "text",
        ["weekend"],
        2,
        ["stardew-valley", "geoguessr", "minecraft"],
        "Geography nerd. I will guess your country from a bush.",
    ),
    (
        "Maks",
        2000,
        "raven",
        "#607D8B",
        ["duo", "friends"],
        "igl",
        "competitive",
        "voice",
        ["evening", "night"],
        4,
        ["dota2", "cs2"],
        "5k MMR, allegedly.",
    ),
    (
        "Zlata",
        2001,
        "vesper",
        "#FF9800",
        ["dating", "friends"],
        "support",
        "casual",
        "voice",
        ["evening"],
        1,
        ["among-us", "overcooked-2", "valorant"],
        "Kind, calm, occasionally the impostor.",
    ),
    (
        "Roman",
        1999,
        "sentinel",
        "#3F51B5",
        ["duo", "dating"],
        "tank",
        "casual",
        "both",
        ["night", "weekend"],
        3,
        ["lol", "it-takes-two", "rocket-league"],
        "Tank in game, soft in real life.",
    ),
]


async def seed() -> None:
    await create_all()
    async with SessionLocal() as s:
        if await s.scalar(select(User.id).where(User.email == "user01@teamate.dev")):
            print("Seed already applied.")
            return

        games: dict[str, Game] = {}
        for name, slug, chill, color in GAMES:
            g = await s.scalar(select(Game).where(Game.slug == slug))
            if g is None:
                g = Game(name=name, slug=slug, is_chill=chill, cover_color=color)
                s.add(g)
            games[slug] = g
        await s.flush()

        users: list[User] = []
        pw = hash_password(PASSWORD)
        for i, (name, year, avatar, accent, modes, role, style, comms, sched, tox, slugs, bio) in enumerate(USERS, 1):
            u = User(
                email=f"user{i:02d}@teamate.dev",
                password_hash=pw,
                display_name=name,
                birth_date=date(year, random.randint(1, 12), random.randint(1, 28)),
                is_premium=(i == 2),
            )
            u.profile = Profile(
                bio=bio,
                avatar_key=AvatarKey(avatar),
                accent_color=accent,
                modes=modes,
                role=role,
                playstyle=style,
                comms=comms,
                schedule=sched,
                toxicity_tolerance=tox,
                games=[ProfileGame(game_id=games[slug].id) for slug in slugs],
            )
            s.add(u)
            users.append(u)
        await s.flush()

        now = datetime.now(UTC)
        open_events = [
            (0, "valorant", "Duo to Diamond tonight", 2, EventKind.squad, 3),
            (1, "cs2", "Premier stack, need 2 more", 5, EventKind.squad, 5),
            (3, "dota2", "Turbo chill after work", 5, EventKind.squad, 4),
            (5, "among-us", "Friday sus night", 8, EventKind.squad, 26),
            (6, "overcooked-2", "Overcooked date, bring patience", 2, EventKind.game_date, 28),
            (7, "apex", "Morning ranked trios", 3, EventKind.squad, 14),
        ]
        for host_idx, slug, title, slots, kind, hours in open_events:
            e = Event(
                host_id=users[host_idx].id,
                game_id=games[slug].id,
                kind=kind,
                title=title,
                starts_at=now + timedelta(hours=hours),
                max_slots=slots,
            )
            e.participants.append(EventParticipant(user_id=users[host_idx].id))
            s.add(e)

        # Two finished events: one already led to a match with messages.
        finished = Event(
            host_id=users[1].id,
            game_id=games["valorant"].id,
            title="Yesterday's duo",
            starts_at=now - timedelta(days=1),
            max_slots=2,
            status=EventStatus.finished,
        )
        finished.participants = [EventParticipant(user_id=users[1].id), EventParticipant(user_id=users[4].id)]
        s.add(finished)

        played = Event(
            host_id=users[2].id,
            game_id=games["minecraft"].id,
            title="Farm build session",
            starts_at=now - timedelta(days=2),
            max_slots=3,
            status=EventStatus.finished,
        )
        played.participants = [
            EventParticipant(user_id=users[2].id),
            EventParticipant(user_id=users[8].id),
            EventParticipant(user_id=users[0].id),
        ]
        s.add(played)
        await s.flush()

        m1 = await create_match(s, users[1].id, users[4].id, MatchSource.post_game)
        m2 = await create_match(s, users[6].id, users[10].id, MatchSource.mutual_like)
        await s.flush()
        s.add_all(
            [
                Message(
                    conversation_id=m1.conversation.id, sender_id=users[4].id, body="ok that last clutch was insane"
                ),
                Message(
                    conversation_id=m1.conversation.id,
                    sender_id=users[1].id,
                    body="you called it, I just clicked heads",
                ),
                Message(
                    conversation_id=m1.conversation.id,
                    sender_id=users[4].id,
                    body="same time tomorrow? loser buys coffee",
                ),
                Message(
                    conversation_id=m2.conversation.id, sender_id=users[10].id, body="hi! overcooked survivor here"
                ),
            ]
        )
        await s.commit()
        print(f"Seeded {len(USERS)} users (password: {PASSWORD}), {len(GAMES)} games, {len(open_events) + 2} events.")


if __name__ == "__main__":
    asyncio.run(seed())
