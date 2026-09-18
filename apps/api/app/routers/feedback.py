import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.schemas.feedback import FeedbackIn, FeedbackResult, PendingFeedbackOut
from app.services import events as events_service
from app.services import feedback as service

router = APIRouter(prefix="/events/{event_id}/feedback", tags=["feedback"])


@router.get("", response_model=PendingFeedbackOut)
async def pending(event_id: uuid.UUID, user: CurrentUser, session: Session) -> PendingFeedbackOut:
    event = await events_service.get_event(session, event_id)
    return await service.pending_feedback(session, event, user)


@router.post("", response_model=FeedbackResult)
async def submit(event_id: uuid.UUID, data: FeedbackIn, user: CurrentUser, session: Session) -> FeedbackResult:
    event = await events_service.get_event(session, event_id)
    return await service.submit_feedback(session, event, user, data.to_user_id, data.answer)
