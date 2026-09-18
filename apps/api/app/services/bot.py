"""Teamate Guide: a scripted companion so a single person can try chat and reveal.

The guide is a normal user row with `is_bot=True`. Everything it does goes through the
same services as a human would, so the client needs no special cases.
"""

import asyncio
import random
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.models import Conversation, Match, MatchSource, Message, User
from app.services.matches import create_match, notify_match

GUIDE_EMAIL = "guide@teamate.dev"
REPLY_DELAY_S = (0.9, 1.8)

_OPENERS = [
    "hey, I'm the guide. I'm here so you can see how chat feels before a real match shows up.",
    "try sending anything. I answer in about a second, and I'll say yes if you ask to reveal photos.",
]

_RULES: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(r"\b(hi|hey|hello|yo|sup|привіт|хай)\b", re.I),
        ["hey! what are you queueing tonight?", "hi. good timing, I just got out of a match."],
    ),
    (
        re.compile(r"\b(valorant|val)\b", re.I),
        ["Valorant duo? I main sentinel, so you can go loud.", "sure, but if we lose pistol round I'm blaming lag."],
    ),
    (
        re.compile(r"\b(dota|lol|league)\b", re.I),
        ["I play support. I will ward, you will not ping me.", "moba night? I'm in, as long as nobody rage-quits."],
    ),
    (
        re.compile(r"\b(among us|sus|impostor)\b", re.I),
        ["you sound sus already.", "I was NOT the impostor last time. mostly."],
    ),
    (
        re.compile(r"\b(reveal|photo|face|look like)\b", re.I),
        [
            "press Reveal in the header and I'll agree on my side. both have to say yes, that's the rule.",
            "photos unlock when both of us tap Reveal. try it.",
        ],
    ),
    (
        re.compile(r"\b(coffee|date|tomorrow|tonight|when)\b", re.I),
        ["tonight after 8 works. bring snacks.", "tomorrow's good. I'll host a Game Date, you just join."],
    ),
    (
        re.compile(r"\?$"),
        [
            "honestly? yes.",
            "good question. short answer: play a round first, then decide.",
            "depends. how tilted are you right now?",
        ],
    ),
    (
        re.compile(r"\b(gg|wp|nice|clutch|insane)\b", re.I),
        ["gg. that last round was yours.", "wp. same time tomorrow?"],
    ),
]

_FALLBACK = [
    "ha, fair.",
    "ok noted. tell me your main game and I'll tell you if we'd survive a ranked game together.",
    "I'm listening. also: the Events tab is where the real matches happen.",
    "say more?",
    "you type like someone who plays support. am I close?",
]


def pick_reply(text: str) -> str:
    for pattern, options in _RULES:
        if pattern.search(text):
            return random.choice(options)
    return random.choice(_FALLBACK)


async def get_guide(session: AsyncSession) -> User | None:
    return await session.scalar(select(User).where(User.email == GUIDE_EMAIL))


async def ensure_guide_match(session: AsyncSession, user: User) -> Match | None:
    """Called when a profile becomes onboarded: match the user with the guide and say hello."""
    guide = await get_guide(session)
    if guide is None or user.id == guide.id:
        return None
    existed = await session.scalar(
        select(Match.id).where(Match.user_a_id.in_([user.id, guide.id]), Match.user_b_id.in_([user.id, guide.id]))
    )
    match = await create_match(session, user.id, guide.id, MatchSource.mutual_like)
    if existed is None:
        for body in _OPENERS:
            session.add(Message(conversation_id=match.conversation.id, sender_id=guide.id, body=body))
    await session.commit()
    if existed is None:
        await notify_match(session, match)
    return match


async def schedule_reply(conv: Conversation, sender_id: uuid.UUID, text: str) -> None:
    """Fire-and-forget: if the other side of this conversation is the guide, reply after a short delay."""
    other_id = conv.match.other_id(sender_id)
    async with SessionLocal() as session:
        other = await session.get(User, other_id)
        if other is None or not other.is_bot:
            return
    asyncio.create_task(_reply_later(conv.id, other_id, text))


async def _reply_later(conversation_id: uuid.UUID, guide_id: uuid.UUID, text: str) -> None:
    from app.services import chat as chat_service

    await asyncio.sleep(random.uniform(*REPLY_DELAY_S))
    async with SessionLocal() as session:
        conv = await session.get(Conversation, conversation_id)
        if conv is None:
            return
        await chat_service.send_message(session, conv, guide_id, pick_reply(text))


async def schedule_consent(match: Match, user_id: uuid.UUID) -> None:
    """When a human consents to reveal in a guide match, the guide agrees a moment later."""
    other_id = match.other_id(user_id)
    async with SessionLocal() as session:
        other = await session.get(User, other_id)
        if other is None or not other.is_bot:
            return
    asyncio.create_task(_consent_later(match.id, other_id))


async def _consent_later(match_id: uuid.UUID, guide_id: uuid.UUID) -> None:
    from app.services import reveal as reveal_service

    await asyncio.sleep(random.uniform(*REPLY_DELAY_S))
    async with SessionLocal() as session:
        match = await session.get(Match, match_id)
        guide = await session.get(User, guide_id)
        if match is None or guide is None:
            return
        if not match.reveal_for(guide_id).consent_next:
            await reveal_service.consent(session, match, guide)
