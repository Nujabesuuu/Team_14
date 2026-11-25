"""US-07, US-19: pure rules of an event in time (BR-06, BR-10, BR-11). Written from requirements, not from code."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain import events as d
from app.models import EventStatus

T0 = datetime(2026, 10, 30, 21, 0, tzinfo=UTC)  # Friday, 21:00 — the start of Taras's event


def test_rule_constants_match_requirements():
    """BR-10, BR-11: 15 minutes of play, 2 confirmations, auto-finish after 3 hours."""
    assert d.MIN_PLAY == timedelta(minutes=15)
    assert d.MIN_CONFIRMATIONS == 2
    assert d.AUTO_FINISH_AFTER == timedelta(hours=3)


@pytest.mark.parametrize(
    "played,confirmations,counted",
    [
        (timedelta(minutes=15), 2, True),
        (timedelta(minutes=45), 2, True),
        (timedelta(minutes=14, seconds=59), 2, False),
        (timedelta(minutes=10), 2, False),
        (timedelta(minutes=45), 1, False),
    ],
    ids=[
        "15 min | both | counted",
        "45 min | both | counted",
        "14 min 59 s | both | not counted",
        "10 min | both | not counted",
        "45 min | only Olena | not counted",
    ],
)
def test_game_counting_rule(played, confirmations, counted):
    """US-07 Scenario Outline: Правило зарахування гри."""
    assert d.game_counts(T0, T0 + played, confirmations) is counted


@pytest.mark.parametrize(
    "played,confirmations,counted",
    [
        (timedelta(minutes=15), 1, False),
        (timedelta(minutes=15), 3, True),
        (timedelta(minutes=15), 0, False),
        (timedelta(hours=3), 2, True),
    ],
    ids=["15 min, 1 confirmation", "15 min, 3 confirmations", "no confirmations", "auto-finished 3 h game"],
)
def test_game_counting_boundaries(played, confirmations, counted):
    """US-07 checklist 1-2: both conditions must hold at once (BR-11)."""
    assert d.game_counts(T0, T0 + played, confirmations) is counted


@pytest.mark.parametrize(
    "since_start,due",
    [
        (timedelta(hours=2, minutes=59, seconds=59), False),
        (timedelta(hours=3), True),
        (timedelta(hours=3, minutes=1), True),
    ],
    ids=["2 h 59 min 59 s", "exactly 3 h", "3 h 1 min"],
)
def test_auto_finish_after_three_hours(since_start, due):
    """US-07 Scenario: Івент завершується сам, якщо хост забув (BR-10)."""
    assert d.auto_finish_due(EventStatus.in_progress, T0, T0 + since_start) is due


@pytest.mark.parametrize(
    "status,started_at",
    [
        (EventStatus.open, None),
        (EventStatus.full, None),
        (EventStatus.finished, T0),
        (EventStatus.cancelled, None),
        (EventStatus.in_progress, None),
    ],
    ids=["open", "full", "already finished", "cancelled", "in_progress without started_at"],
)
def test_auto_finish_only_for_running_events(status, started_at):
    """US-07, BR-10: only a started, still running event is finished by the timer."""
    assert d.auto_finish_due(status, started_at, T0 + timedelta(hours=10)) is False


@pytest.mark.parametrize(
    "starts_at,in_past",
    [
        (T0 - timedelta(hours=1), True),
        (T0 - timedelta(minutes=1), True),
        (T0, False),
        (T0 + timedelta(minutes=1), False),
    ],
    ids=["Friday 20:00 at 21:00", "one minute ago", "right now", "in one minute"],
)
def test_start_time_in_past(starts_at, in_past):
    """US-19 Scenario: Час початку в минулому (BR-06)."""
    assert d.starts_in_past(starts_at, T0) is in_past
