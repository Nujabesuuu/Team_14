from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import reveal as rules
from app.models import Match, User
from app.services.matches import match_out
from app.ws.hub import hub


async def _push(session: AsyncSession, match: Match) -> None:
    for uid in (match.user_a_id, match.user_b_id):
        viewer = await session.get(User, uid)
        out = await match_out(session, match, viewer)
        await hub.send_to_user(uid, {"type": "reveal.updated", "match": out.model_dump(mode="json")})


async def consent(session: AsyncSession, match: Match, user: User) -> Match:
    mine = match.reveal_for(user.id)
    theirs = match.reveal_for(match.other_id(user.id))
    mine.consent_next = True
    if rules.stage_after_consent(mine.stage, mine.consent_next, theirs.consent_next) == rules.CLEAR:
        mine.stage = theirs.stage = rules.CLEAR
    await session.commit()
    await _push(session, match)
    return match


async def early_request(session: AsyncSession, match: Match, user: User) -> Match:
    if not user.is_premium:
        raise ApiError(402, "PREMIUM_REQUIRED", "Early reveal requests are a Teamate+ feature")
    match.reveal_for(user.id).early_request = True
    await session.commit()
    await _push(session, match)
    return match


async def early_accept(session: AsyncSession, match: Match, user: User) -> Match:
    theirs = match.reveal_for(match.other_id(user.id))
    if not theirs.early_request:
        raise ApiError(409, "NO_EARLY_REQUEST", "There is no early reveal request to accept")
    for r in match.reveals:
        r.stage = rules.CLEAR
        r.consent_next = True
        r.early_request = False
    await session.commit()
    await _push(session, match)
    return match
