import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import feedback as rules
from app.domain.matching import match_after_feedback
from app.models import Event, EventStatus, FeedbackAnswer, MatchSource, PostGameFeedback, User
from app.models._base import utcnow
from app.schemas.common import PublicUser
from app.schemas.feedback import FeedbackResult, PendingFeedbackOut
from app.services.blocks import blocked_ids
from app.services.events import lock
from app.services.matches import insert_match, notify_match


def _assert_counted_participant(event: Event, user_id: uuid.UUID) -> None:
    if user_id not in event.participant_ids:
        raise ApiError(403, "NOT_PARTICIPANT", "You did not take part in this event")
    if event.status != EventStatus.finished:
        raise ApiError(409, "EVENT_NOT_FINISHED", "Feedback opens once the event is finished")
    # US-07: a game shorter than 15 min or with fewer than 2 confirmations never asks "Play again?".
    if event.counted_at is None:
        raise ApiError(409, "GAME_NOT_COUNTED", "This game was not counted, so there is no Play again? for it")


async def pending_feedback(session: AsyncSession, event: Event, user: User) -> PendingFeedbackOut:
    _assert_counted_participant(event, user.id)
    done = set(
        (
            await session.scalars(
                select(PostGameFeedback.to_user_id).where(
                    PostGameFeedback.event_id == event.id, PostGameFeedback.from_user_id == user.id
                )
            )
        ).all()
    )
    # A block after the game hides the person here too (BR-21), like a moderator's ban does.
    hidden = await blocked_ids(session, user.id)
    teammates = [
        p.user
        for p in event.participants
        if p.user_id != user.id and p.user_id not in done and p.user_id not in hidden and not p.user.is_banned
    ]
    return PendingFeedbackOut(
        pending=[PublicUser.from_user(t) for t in teammates],
        done=sorted(done, key=str),
        closer_allowed={t.id: rules.closer_allowed(user.profile.modes, t.profile.modes) for t in teammates},
    )


async def submit_feedback(
    session: AsyncSession, event: Event, user: User, to_user_id: uuid.UUID, answer: FeedbackAnswer
) -> FeedbackResult:
    _assert_counted_participant(event, user.id)
    if not rules.feedback_open(event.counted_at, utcnow()):
        raise ApiError(409, "FEEDBACK_WINDOW_CLOSED", "The 24 hours to answer have passed")
    if to_user_id == user.id or to_user_id not in event.participant_ids:
        raise ApiError(422, "NOT_A_TEAMMATE", "You can only rate people who played this event with you")

    await lock(session, event)
    existing = await session.scalar(
        select(PostGameFeedback).where(
            PostGameFeedback.event_id == event.id,
            PostGameFeedback.from_user_id == user.id,
            PostGameFeedback.to_user_id == to_user_id,
        )
    )
    if existing is not None:
        raise ApiError(409, "ALREADY_RATED", "You already answered for this teammate")

    target = next(p.user for p in event.participants if p.user_id == to_user_id)
    # Checked against both current settings: if either side turned dating off after the other said "closer",
    # the second "closer" is refused and no match can appear (US-12).
    if answer == FeedbackAnswer.closer and not rules.closer_allowed(user.profile.modes, target.profile.modes):
        raise ApiError(422, "CLOSER_REQUIRES_DATING", "Get closer is available only when you both have Dating on")

    # Banned or blocked on either side: nothing is stored and no match can appear, but the answer looks like an
    # ordinary "no match yet" — a distinct error would tell the blocked person about the block (NEVER-05).
    if target.is_banned or to_user_id in await blocked_ids(session, user.id):
        return FeedbackResult(match_created=False)

    session.add(PostGameFeedback(event_id=event.id, from_user_id=user.id, to_user_id=to_user_id, answer=answer))
    await session.flush()
    theirs = await session.scalar(
        select(PostGameFeedback.answer).where(
            PostGameFeedback.event_id == event.id,
            PostGameFeedback.from_user_id == to_user_id,
            PostGameFeedback.to_user_id == user.id,
        )
    )
    if not match_after_feedback(answer, theirs):
        await session.commit()
        return FeedbackResult(match_created=False)

    match, created = await insert_match(session, user.id, to_user_id, MatchSource.post_game)
    await session.commit()
    # Both "closer" at the same moment: both learn there is a match, but match.new goes out once, from the creator.
    if created:
        await notify_match(session, match)
    return FeedbackResult(match_created=True, match_id=match.id)
