import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.models import EventKind, EventStatus
from app.schemas.event import EventCreate, EventOut
from app.services import events as service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
async def list_events(
    user: CurrentUser,
    session: Session,
    game_id: uuid.UUID | None = None,
    kind: EventKind | None = None,
    status: EventStatus | None = None,
    mine: bool = False,
) -> list[EventOut]:
    events = await service.list_events(session, user, game_id=game_id, kind=kind, status=status, mine=mine)
    return [EventOut.from_event(e, user.id) for e in events]


@router.post("", response_model=EventOut, status_code=201)
async def create_event(data: EventCreate, user: CurrentUser, session: Session) -> EventOut:
    return EventOut.from_event(await service.create_event(session, user, data), user.id)


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    return EventOut.from_event(await service.get_event(session, event_id), user.id)


@router.post("/{event_id}/join", response_model=EventOut)
async def join(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    event = await service.get_event(session, event_id)
    return EventOut.from_event(await service.join_event(session, event, user), user.id)


@router.post("/{event_id}/leave", response_model=EventOut)
async def leave(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    event = await service.get_event(session, event_id)
    return EventOut.from_event(await service.leave_event(session, event, user), user.id)


@router.post("/{event_id}/start", response_model=EventOut)
async def start(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    event = await service.get_event(session, event_id)
    return EventOut.from_event(await service.transition_event(session, event, user, "start"), user.id)


@router.post("/{event_id}/finish", response_model=EventOut)
async def finish(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    event = await service.get_event(session, event_id)
    return EventOut.from_event(await service.transition_event(session, event, user, "finish"), user.id)


@router.post("/{event_id}/cancel", response_model=EventOut)
async def cancel(event_id: uuid.UUID, user: CurrentUser, session: Session) -> EventOut:
    event = await service.get_event(session, event_id)
    return EventOut.from_event(await service.transition_event(session, event, user, "cancel"), user.id)
