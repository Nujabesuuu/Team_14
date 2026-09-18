import uuid
from itertools import combinations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import events as rules
from app.domain import reveal as reveal_rules
from app.models import Event, EventKind, EventParticipant, EventStatus, Game, User
from app.schemas.event import EventCreate, EventOut
from app.services.blocks import blocked_ids
from app.services.matches import find_match
from app.ws.hub import hub

_STATUS_ERRORS = {
    "ALREADY_JOINED": (409, "You already joined this event"),
    "EVENT_FULL": (409, "This event is full"),
    "EVENT_NOT_OPEN": (409, "This event is no longer open"),
    "NOT_PARTICIPANT": (409, "You are not in this event"),
    "HOST_CANNOT_LEAVE": (409, "The host cannot leave; cancel the event instead"),
    "EVENT_STARTED": (409, "The event already started"),
    "HOST_ONLY": (403, "Only the host can do this"),
    "INVALID_TRANSITION": (409, "This action is not possible in the current state"),
    "GAME_DATE_REQUIRES_CHILL_GAME": (422, "Game Date needs a chill game"),
    "GAME_DATE_REQUIRES_DATING_MODE": (422, "Enable Dating mode (18+) to host a Game Date"),
}


def _raise(code: str) -> None:
    status, detail = _STATUS_ERRORS[code]
    raise ApiError(status, code, detail)


async def get_event(session: AsyncSession, event_id: uuid.UUID) -> Event:
    event = await session.get(Event, event_id)
    if event is None:
        raise ApiError(404, "EVENT_NOT_FOUND", "Event not found")
    return event


async def _broadcast(session: AsyncSession, event: Event) -> None:
    await session.refresh(event)
    for uid in event.participant_ids:
        viewer_out = EventOut.from_event(event, uid)
        await hub.send_to_user(uid, {"type": "event.updated", "event": viewer_out.model_dump(mode="json")})


async def create_event(session: AsyncSession, host: User, data: EventCreate) -> Event:
    game = await session.get(Game, data.game_id)
    if game is None:
        raise ApiError(422, "UNKNOWN_GAME", "Unknown game")
    error = rules.validate_new_event(data.kind, game.is_chill, host.profile.modes, host.age)
    if error:
        _raise(error)
    event = Event(
        host_id=host.id,
        game_id=game.id,
        kind=data.kind,
        title=data.title.strip(),
        starts_at=data.starts_at,
        max_slots=rules.slots_for(data.kind, data.max_slots),
    )
    event.participants.append(EventParticipant(user_id=host.id))
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def list_events(
    session: AsyncSession,
    viewer: User,
    *,
    game_id: uuid.UUID | None = None,
    kind: EventKind | None = None,
    status: EventStatus | None = None,
    mine: bool = False,
) -> list[Event]:
    q = select(Event).order_by(desc(Event.created_at))
    if game_id:
        q = q.where(Event.game_id == game_id)
    if kind:
        q = q.where(Event.kind == kind)
    if status:
        q = q.where(Event.status == status)
    elif not mine:
        q = q.where(Event.status.in_([EventStatus.open, EventStatus.full, EventStatus.in_progress]))
    events = (await session.scalars(q)).all()

    hidden = await blocked_ids(session, viewer.id)
    out = []
    for e in events:
        if mine and viewer.id not in e.participant_ids:
            continue
        if e.host_id in hidden:
            continue
        if not rules.event_visible(e.kind, viewer.profile.modes, viewer.age):
            continue
        out.append(e)
    return out


async def join_event(session: AsyncSession, event: Event, user: User) -> Event:
    if not rules.event_visible(event.kind, user.profile.modes, user.age):
        raise ApiError(403, "EVENT_NOT_VISIBLE", "This event is not available to you")
    if event.host_id in await blocked_ids(session, user.id):
        raise ApiError(403, "BLOCKED", "You cannot join this event")
    error = rules.can_join(event.status, len(event.participants), event.max_slots, user.id in event.participant_ids)
    if error:
        _raise(error)
    event.participants.append(EventParticipant(user_id=user.id))
    event.status = rules.next_status_after_join(len(event.participants), event.max_slots)
    await session.commit()
    await _broadcast(session, event)
    return event


async def leave_event(session: AsyncSession, event: Event, user: User) -> Event:
    error = rules.can_leave(event.status, event.host_id == user.id, user.id in event.participant_ids)
    if error:
        _raise(error)
    event.participants = [p for p in event.participants if p.user_id != user.id]
    event.status = EventStatus.open
    await session.commit()
    await _broadcast(session, event)
    return event


async def transition_event(session: AsyncSession, event: Event, user: User, action: rules.Action) -> Event:
    new_status, error = rules.transition(event.status, action, event.host_id == user.id)
    if error:
        _raise(error)
    event.status = new_status
    if action == "finish":
        await _unlock_reveals_for_matched_pairs(session, event)
    await session.commit()
    await _broadcast(session, event)
    return event


async def _unlock_reveals_for_matched_pairs(session: AsyncSession, event: Event) -> None:
    """Playing together after matching moves both photos to the PLAYED reveal stage."""
    for a, b in combinations(event.participant_ids, 2):
        match = await find_match(session, a, b)
        if match is None:
            continue
        for r in match.reveals:
            r.stage = reveal_rules.stage_after_shared_event(r.stage)
        await hub.send_to_users((a, b), {"type": "reveal.updated", "match_id": str(match.id)})
