import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain.matching import match_after_feedback
from app.models import Event, EventStatus, FeedbackAnswer, MatchSource, PostGameFeedback, User
from app.schemas.common import PublicUser
from app.schemas.feedback import FeedbackResult, PendingFeedbackOut
from app.services.matches import create_match, notify_match


def _assert_finished_participant(event: Event, user_id: uuid.UUID) -> None:
    if user_id not in event.participant_ids:
        raise ApiError(403, "NOT_PARTICIPANT", "You did not take part in this event")
    if event.status != EventStatus.finished:
        raise ApiError(409, "EVENT_NOT_FINISHED", "Feedback opens once the event is finished")


async def pending_feedback(session: AsyncSession, event: Event, user: User) -> PendingFeedbackOut:
    _assert_finished_participant(event, user.id)
    done = set(
        (
            await session.scalars(
                select(PostGameFeedback.to_user_id).where(
                    PostGameFeedback.event_id == event.id, PostGameFeedback.from_user_id == user.id
                )
            )
        ).all()
    )
    pending = [
        PublicUser.from_user(p.user) for p in event.participants if p.user_id != user.id and p.user_id not in done
    ]
    return PendingFeedbackOut(pending=pending, done=sorted(done, key=str))


async def submit_feedback(
    session: AsyncSession, event: Event, user: User, to_user_id: uuid.UUID, answer: FeedbackAnswer
) -> FeedbackResult:
    _assert_finished_participant(event, user.id)
    if to_user_id == user.id or to_user_id not in event.participant_ids:
        raise ApiError(422, "NOT_A_TEAMMATE", "You can only rate people who played this event with you")

    existing = await session.scalar(
        select(PostGameFeedback).where(
            PostGameFeedback.event_id == event.id,
            PostGameFeedback.from_user_id == user.id,
            PostGameFeedback.to_user_id == to_user_id,
        )
    )
    if existing is not None:
        raise ApiError(409, "ALREADY_RATED", "You already answered for this teammate")

    session.add(PostGameFeedback(event_id=event.id, from_user_id=user.id, to_user_id=to_user_id, answer=answer))

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

    match = await create_match(session, user.id, to_user_id, MatchSource.post_game)
    await session.commit()
    await notify_match(session, match)
    return FeedbackResult(match_created=True, match_id=match.id)
