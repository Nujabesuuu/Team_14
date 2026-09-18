import pytest

from app.domain import events as d
from app.models.enums import EventKind, EventStatus


def test_join_fills_event():
    assert d.next_status_after_join(participants=1, max_slots=2) == EventStatus.open
    assert d.next_status_after_join(participants=2, max_slots=2) == EventStatus.full


@pytest.mark.parametrize(
    "status,participants,is_participant,expected",
    [
        (EventStatus.open, 1, False, None),
        (EventStatus.open, 1, True, "ALREADY_JOINED"),
        (EventStatus.full, 2, False, "EVENT_FULL"),
        (EventStatus.in_progress, 1, False, "EVENT_NOT_OPEN"),
        (EventStatus.cancelled, 1, False, "EVENT_NOT_OPEN"),
    ],
)
def test_can_join(status, participants, is_participant, expected):
    assert d.can_join(status, participants, 2, is_participant) == expected


def test_host_cannot_leave_and_nobody_leaves_after_start():
    assert d.can_leave(EventStatus.open, is_host=True, is_participant=True) == "HOST_CANNOT_LEAVE"
    assert d.can_leave(EventStatus.in_progress, is_host=False, is_participant=True) == "EVENT_STARTED"
    assert d.can_leave(EventStatus.open, is_host=False, is_participant=False) == "NOT_PARTICIPANT"
    assert d.can_leave(EventStatus.full, is_host=False, is_participant=True) is None


@pytest.mark.parametrize(
    "status,action,expected",
    [
        (EventStatus.open, "start", EventStatus.in_progress),
        (EventStatus.full, "start", EventStatus.in_progress),
        (EventStatus.in_progress, "finish", EventStatus.finished),
        (EventStatus.open, "cancel", EventStatus.cancelled),
    ],
)
def test_valid_transitions(status, action, expected):
    assert d.transition(status, action, is_host=True) == (expected, None)


@pytest.mark.parametrize(
    "status,action",
    [
        (EventStatus.open, "finish"),
        (EventStatus.finished, "start"),
        (EventStatus.in_progress, "cancel"),
        (EventStatus.cancelled, "start"),
    ],
)
def test_invalid_transitions(status, action):
    assert d.transition(status, action, is_host=True) == (None, "INVALID_TRANSITION")


def test_only_host_transitions():
    assert d.transition(EventStatus.open, "start", is_host=False) == (None, "HOST_ONLY")


def test_game_date_visibility():
    assert d.event_visible(EventKind.squad, [], 15) is True
    assert d.event_visible(EventKind.game_date, ["duo"], 25) is False
    assert d.event_visible(EventKind.game_date, ["dating"], 17) is False
    assert d.event_visible(EventKind.game_date, ["dating"], 18) is True


def test_new_game_date_validation():
    assert d.validate_new_event(EventKind.game_date, False, ["dating"], 20) == "GAME_DATE_REQUIRES_CHILL_GAME"
    assert d.validate_new_event(EventKind.game_date, True, ["duo"], 20) == "GAME_DATE_REQUIRES_DATING_MODE"
    assert d.validate_new_event(EventKind.game_date, True, ["dating"], 20) is None
    assert d.validate_new_event(EventKind.squad, False, [], 15) is None


def test_slots():
    assert d.slots_for(EventKind.game_date, 5) == 2
    assert d.slots_for(EventKind.squad, 1) == 2
    assert d.slots_for(EventKind.squad, 50) == 10
