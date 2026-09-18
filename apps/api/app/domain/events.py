"""Pure rules for the event lifecycle. No I/O, no ORM: easy to test and reason about.

State machine:
    open --(slots filled)--> full
    open/full --(host: start)--> in_progress --(host: finish)--> finished
    open/full --(host: cancel)--> cancelled
"""

from typing import Literal

from app.models.enums import EventKind, EventStatus, Mode

Action = Literal["start", "finish", "cancel"]
ADULT_AGE = 18


def next_status_after_join(participants: int, max_slots: int) -> EventStatus:
    return EventStatus.full if participants >= max_slots else EventStatus.open


def can_join(status: EventStatus, participants: int, max_slots: int, is_participant: bool) -> str | None:
    """Return an error code if joining is not allowed, otherwise None."""
    if is_participant:
        return "ALREADY_JOINED"
    if status != EventStatus.open:
        return "EVENT_FULL" if status == EventStatus.full else "EVENT_NOT_OPEN"
    if participants >= max_slots:
        return "EVENT_FULL"
    return None


def can_leave(status: EventStatus, is_host: bool, is_participant: bool) -> str | None:
    if not is_participant:
        return "NOT_PARTICIPANT"
    if is_host:
        return "HOST_CANNOT_LEAVE"
    if status not in (EventStatus.open, EventStatus.full):
        return "EVENT_STARTED"
    return None


_TRANSITIONS: dict[Action, tuple[set[EventStatus], EventStatus]] = {
    "start": ({EventStatus.open, EventStatus.full}, EventStatus.in_progress),
    "finish": ({EventStatus.in_progress}, EventStatus.finished),
    "cancel": ({EventStatus.open, EventStatus.full}, EventStatus.cancelled),
}


def transition(status: EventStatus, action: Action, is_host: bool) -> tuple[EventStatus | None, str | None]:
    """Return (new_status, None) or (None, error_code)."""
    if not is_host:
        return None, "HOST_ONLY"
    allowed_from, target = _TRANSITIONS[action]
    if status not in allowed_from:
        return None, "INVALID_TRANSITION"
    return target, None


def event_visible(kind: EventKind, viewer_modes: list[str], viewer_age: int) -> bool:
    """Game Date events exist only for adults who opted into dating."""
    if kind == EventKind.game_date:
        return Mode.dating in viewer_modes and viewer_age >= ADULT_AGE
    return True


def validate_new_event(kind: EventKind, game_is_chill: bool, host_modes: list[str], host_age: int) -> str | None:
    if kind == EventKind.game_date:
        if not game_is_chill:
            return "GAME_DATE_REQUIRES_CHILL_GAME"
        if not event_visible(kind, host_modes, host_age):
            return "GAME_DATE_REQUIRES_DATING_MODE"
    return None


def slots_for(kind: EventKind, requested: int) -> int:
    return 2 if kind == EventKind.game_date else max(2, min(requested, 10))
