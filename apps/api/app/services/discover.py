import uuid
from datetime import UTC, datetime, time

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.domain import matching as rules
from app.domain.compatibility import score
from app.models import Match, MatchSource, Mode, Swipe, SwipeDirection, User
from app.schemas.common import PublicUser
from app.schemas.discover import DiscoverCard, DiscoverOut, SwipeResult
from app.schemas.profile import ProfileGameOut
from app.services.blocks import blocked_ids
from app.services.matches import create_match, notify_match
from app.services.profile import dna_of

DECK_SIZE = 20


async def _rights_today(session: AsyncSession, user_id: uuid.UUID) -> int:
    start = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    return (
        await session.scalar(
            select(func.count(Swipe.id)).where(
                Swipe.from_user_id == user_id,
                Swipe.direction == SwipeDirection.right,
                Swipe.created_at >= start,
            )
        )
    ) or 0


async def _excluded_ids(session: AsyncSession, viewer_id: uuid.UUID) -> set[uuid.UUID]:
    swiped = set((await session.scalars(select(Swipe.to_user_id).where(Swipe.from_user_id == viewer_id))).all())
    matched_rows = (
        await session.execute(
            select(Match.user_a_id, Match.user_b_id).where(
                or_(Match.user_a_id == viewer_id, Match.user_b_id == viewer_id)
            )
        )
    ).all()
    matched = {b if a == viewer_id else a for a, b in matched_rows}
    return swiped | matched | await blocked_ids(session, viewer_id) | {viewer_id}


def _card(viewer: User, other: User) -> DiscoverCard:
    p = other.profile
    return DiscoverCard(
        user=PublicUser.from_user(other),
        bio=p.bio,
        modes=list(p.modes),
        role=p.role,
        playstyle=p.playstyle,
        comms=p.comms,
        schedule=list(p.schedule),
        games=[ProfileGameOut(id=pg.game.id, name=pg.game.name, slug=pg.game.slug, rank=pg.rank) for pg in p.games],
        compatibility=score(dna_of(viewer.profile), dna_of(p)),
    )


async def discover(session: AsyncSession, viewer: User, mode: Mode) -> DiscoverOut:
    if mode not in viewer.profile.modes:
        raise ApiError(422, "MODE_NOT_ENABLED", f"Enable '{mode}' mode in your profile first")
    excluded = await _excluded_ids(session, viewer.id)
    candidates = (await session.scalars(select(User).where(User.id.not_in(excluded)))).all()
    cards = [
        _card(viewer, u)
        for u in candidates
        if u.profile.onboarded and rules.can_see_in_mode(mode, viewer.age, u.profile.modes, u.age)
    ]
    cards.sort(key=lambda c: c.compatibility, reverse=True)
    limit = get_settings().free_daily_swipes
    return DiscoverOut(
        cards=cards[:DECK_SIZE],
        rights_left=rules.rights_left(viewer.is_premium, await _rights_today(session, viewer.id), limit),
    )


async def swipe(session: AsyncSession, viewer: User, to_user_id: uuid.UUID, direction: SwipeDirection) -> SwipeResult:
    if to_user_id == viewer.id:
        raise ApiError(422, "CANNOT_SWIPE_SELF", "Nice try")
    target = await session.get(User, to_user_id)
    if target is None:
        raise ApiError(404, "USER_NOT_FOUND", "User not found")
    if not rules.share_mode(viewer.profile.modes, target.profile.modes):
        raise ApiError(422, "NO_SHARED_MODE", "You do not share a mode with this person")
    if to_user_id in await blocked_ids(session, viewer.id):
        raise ApiError(403, "BLOCKED", "You cannot interact with this person")

    limit = get_settings().free_daily_swipes
    rights_today = await _rights_today(session, viewer.id)
    if direction == SwipeDirection.right:
        error = rules.can_swipe_right(viewer.is_premium, rights_today, limit)
        if error:
            raise ApiError(429, error, "Daily like limit reached. Teamate+ removes the limit.")

    existing = await session.scalar(
        select(Swipe).where(Swipe.from_user_id == viewer.id, Swipe.to_user_id == to_user_id)
    )
    if existing is not None:
        raise ApiError(409, "ALREADY_SWIPED", "You already swiped this profile")
    session.add(Swipe(from_user_id=viewer.id, to_user_id=to_user_id, direction=direction))

    theirs = await session.scalar(
        select(Swipe.direction).where(Swipe.from_user_id == to_user_id, Swipe.to_user_id == viewer.id)
    )
    rights_after = rights_today + (1 if direction == SwipeDirection.right else 0)
    left = rules.rights_left(viewer.is_premium, rights_after, limit)

    if not rules.match_after_swipe(direction, theirs):
        await session.commit()
        return SwipeResult(match_created=False, rights_left=left)

    match = await create_match(session, viewer.id, to_user_id, MatchSource.mutual_like)
    await session.commit()
    await notify_match(session, match)
    return SwipeResult(match_created=True, match_id=match.id, rights_left=left)


async def undo_last_swipe(session: AsyncSession, viewer: User) -> None:
    last = await session.scalar(
        select(Swipe).where(Swipe.from_user_id == viewer.id).order_by(desc(Swipe.created_at)).limit(1)
    )
    if last is None:
        raise ApiError(404, "NOTHING_TO_UNDO", "No swipe to undo")
    await session.delete(last)
    await session.commit()


async def incoming_likes(session: AsyncSession, viewer: User) -> list[DiscoverCard]:
    excluded = await _excluded_ids(session, viewer.id)
    likers = (
        await session.scalars(
            select(User)
            .join(Swipe, Swipe.from_user_id == User.id)
            .where(Swipe.to_user_id == viewer.id, Swipe.direction == SwipeDirection.right)
            .order_by(desc(Swipe.created_at))
        )
    ).all()
    return [_card(viewer, u) for u in likers if u.id not in excluded]
