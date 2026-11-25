import uuid
from datetime import datetime
from itertools import combinations

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import events as rules
from app.domain import reveal as reveal_rules
from app.models import Event, EventKind, EventParticipant, EventStatus, Game, GameConfirmation, User
from app.models._base import as_utc, utcnow
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
    "STARTS_IN_PAST": (422, "This start time has already passed"),
}


def _raise(code: str) -> None:
    status, detail = _STATUS_ERRORS[code]
    raise ApiError(status, code, detail)


async def get_event(session: AsyncSession, event_id: uuid.UUID) -> Event:
    event = await session.get(Event, event_id)
    if event is None:
        raise ApiError(404, "EVENT_NOT_FOUND", "Event not found")
    changed = await _settle_auto_finish(session, [event])
    # Self-healing for confirmations that raced each other (see confirm_game): the next read counts the game.
    if not changed and await _count_if_due(session, event):
        await session.commit()
        changed = [event]
    for e in changed:
        await broadcast(session, e)
    return event


async def lock(session: AsyncSession, event: Event) -> None:
    """Serialises writes about one event (confirmations, "Play again?" answers). PostgreSQL takes a row lock;
    SQLite ignores FOR UPDATE, but it allows only one writer at a time anyway."""
    await session.execute(select(Event.id).where(Event.id == event.id).with_for_update())


async def _settle_auto_finish(session: AsyncSession, events: list[Event]) -> list[Event]:
    """BR-10 without a scheduler (A-09): whoever reads an overdue event first finishes it at started_at + 3 h.
    Returns the events it finished, so the caller can tell their participants (WS event.updated)."""
    now = utcnow()
    due = [e for e in events if rules.auto_finish_due(e.status, e.started_at, now)]
    for event in due:
        await _mark_finished(session, event, event.started_at + rules.AUTO_FINISH_AFTER)
    if due:
        await session.commit()
    return due


async def _count_if_due(session: AsyncSession, event: Event) -> bool:
    """BR-11, counted from the stored confirmations rather than the in-memory list: two people confirming at the
    same moment each saw only their own row, and the game stayed uncounted forever."""
    if event.counted_at is not None or event.started_at is None or event.finished_at is None:
        return False
    confirmations = await session.scalar(
        select(func.count()).select_from(GameConfirmation).where(GameConfirmation.event_id == event.id)
    )
    if not rules.game_counts(event.started_at, event.finished_at, confirmations or 0):
        return False
    event.counted_at = utcnow()
    return True


async def _mark_finished(session: AsyncSession, event: Event, at: datetime) -> None:
    event.status = EventStatus.finished
    event.finished_at = at
    await _unlock_reveals_for_matched_pairs(session, event)


async def broadcast(session: AsyncSession, event: Event) -> None:
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
    starts_at = as_utc(data.starts_at)
    if rules.starts_in_past(starts_at, utcnow()):
        _raise("STARTS_IN_PAST")
    event = Event(
        host_id=host.id,
        game_id=game.id,
        kind=data.kind,
        title=data.title.strip(),
        starts_at=starts_at,
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
    overdue = select(Event).where(
        Event.status == EventStatus.in_progress, Event.started_at <= utcnow() - rules.AUTO_FINISH_AFTER
    )
    for finished in await _settle_auto_finish(session, list((await session.scalars(overdue)).all())):
        await broadcast(session, finished)

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
    # A block gives the very same answer as an event the person simply may not see (NEVER-05): a distinct code
    # would tell the blocked person that they were blocked.
    if not rules.event_visible(event.kind, user.profile.modes, user.age) or event.host_id in await blocked_ids(
        session, user.id
    ):
        raise ApiError(403, "EVENT_NOT_VISIBLE", "This event is not available to you")
    error = rules.can_join(event.status, len(event.participants), event.max_slots, user.id in event.participant_ids)
    if error:
        _raise(error)
    event.participants.append(EventParticipant(user_id=user.id))
    event.status = rules.next_status_after_join(len(event.participants), event.max_slots)
    await session.commit()
    await broadcast(session, event)
    return event


async def leave_event(session: AsyncSession, event: Event, user: User) -> Event:
    error = rules.can_leave(event.status, event.host_id == user.id, user.id in event.participant_ids)
    if error:
        _raise(error)
    event.participants = [p for p in event.participants if p.user_id != user.id]
    event.status = EventStatus.open
    await session.commit()
    await broadcast(session, event)
    return event


async def transition_event(session: AsyncSession, event: Event, user: User, action: rules.Action) -> Event:
    new_status, error = rules.transition(event.status, action, event.host_id == user.id)
    if error:
        _raise(error)
    if action == "start":
        event.started_at = utcnow()
    if action == "finish":
        await _mark_finished(session, event, utcnow())
    event.status = new_status
    await session.commit()
    await broadcast(session, event)
    return event


async def confirm_game(session: AsyncSession, event: Event, user: User) -> Event:
    """US-07: a participant confirms the game happened; the second confirmation of a long enough game counts it."""
    if user.id not in event.participant_ids:
        raise ApiError(403, "NOT_PARTICIPANT", "You did not take part in this event")
    if event.status != EventStatus.finished:
        raise ApiError(409, "EVENT_NOT_FINISHED", "You can confirm the game once the event is finished")
    if user.id in event.confirmed_ids:
        raise ApiError(409, "ALREADY_CONFIRMED", "You already confirmed this game")
    await lock(session, event)
    try:
        async with session.begin_nested():
            session.add(GameConfirmation(event_id=event.id, user_id=user.id))
    except IntegrityError:
        # A double click: the first request already stored this person's confirmation (PK event_id + user_id).
        raise ApiError(409, "ALREADY_CONFIRMED", "You already confirmed this game") from None
    await _count_if_due(session, event)
    await session.commit()
    await session.refresh(event, ["confirmations"])
    await broadcast(session, event)
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
