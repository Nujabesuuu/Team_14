import uuid

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import reveal as reveal_rules
from app.domain.compatibility import score
from app.models import Conversation, Match, MatchSource, Message, PhotoReveal, User, canonical_pair
from app.schemas.common import PublicUser
from app.schemas.match import MatchOut, MessageOut, RevealState
from app.services.profile import dna_of
from app.ws.hub import hub


async def find_match(session: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> Match | None:
    ua, ub = canonical_pair(a, b)
    return await session.scalar(select(Match).where(Match.user_a_id == ua, Match.user_b_id == ub))


async def create_match(session: AsyncSession, a: uuid.UUID, b: uuid.UUID, source: MatchSource) -> Match:
    """Idempotent: returns the existing match if the pair already matched (by any path)."""
    existing = await find_match(session, a, b)
    if existing is not None:
        return existing
    ua, ub = canonical_pair(a, b)
    match = Match(user_a_id=ua, user_b_id=ub, source=source)
    match.reveals = [
        PhotoReveal(user_id=ua, stage=reveal_rules.stage_after_match()),
        PhotoReveal(user_id=ub, stage=reveal_rules.stage_after_match()),
    ]
    match.conversation = Conversation()
    session.add(match)
    await session.flush()
    return match


async def notify_match(session: AsyncSession, match: Match) -> None:
    for uid in (match.user_a_id, match.user_b_id):
        viewer = await session.get(User, uid)
        out = await match_out(session, match, viewer)
        await hub.send_to_user(uid, {"type": "match.new", "match": out.model_dump(mode="json")})


def reveal_state(match: Match, viewer_id: uuid.UUID) -> RevealState:
    mine = match.reveal_for(viewer_id)
    theirs = match.reveal_for(match.other_id(viewer_id))
    return RevealState(
        my_stage=mine.stage,
        their_stage=theirs.stage,
        my_consent=mine.consent_next,
        their_consent=theirs.consent_next,
        early_request_from_me=mine.early_request,
        early_request_from_them=theirs.early_request,
    )


async def last_message(session: AsyncSession, conversation_id: uuid.UUID) -> Message | None:
    return await session.scalar(
        select(Message).where(Message.conversation_id == conversation_id).order_by(desc(Message.created_at)).limit(1)
    )


async def match_out(session: AsyncSession, match: Match, viewer: User) -> MatchOut:
    other = match.user_b if viewer.id == match.user_a_id else match.user_a
    msg = await last_message(session, match.conversation.id)
    return MatchOut(
        id=match.id,
        other=PublicUser.from_user(other),
        source=match.source,
        conversation_id=match.conversation.id,
        reveal=reveal_state(match, viewer.id),
        compatibility=score(dna_of(viewer.profile), dna_of(other.profile)),
        last_message=MessageOut.model_validate(msg, from_attributes=True) if msg else None,
        created_at=match.created_at,
    )


async def list_matches(session: AsyncSession, viewer: User) -> list[MatchOut]:
    matches = (
        await session.scalars(
            select(Match)
            .where(or_(Match.user_a_id == viewer.id, Match.user_b_id == viewer.id))
            .order_by(desc(Match.created_at))
        )
    ).all()
    return [await match_out(session, m, viewer) for m in matches]


async def get_match_for(session: AsyncSession, match_id: uuid.UUID, viewer_id: uuid.UUID) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise ApiError(404, "MATCH_NOT_FOUND", "Match not found")
    if not match.involves(viewer_id):
        raise ApiError(403, "NOT_YOUR_MATCH", "You are not part of this match")
    return match
