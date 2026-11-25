"""US-11, US-12: pure rules of «Зіграємо ще?» (BR-12, BR-13, BR-14). Written from requirements, not from code."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain import feedback as f
from app.domain import matching as m
from app.models import FeedbackAnswer as F

COUNTED = datetime(2026, 10, 30, 22, 0, tzinfo=UTC)  # game counted on Friday at 22:00


def test_window_is_24_hours():
    """BR-12: 24 hours from the moment the game was counted."""
    assert f.FEEDBACK_WINDOW == timedelta(hours=24)


def test_window_closes_24_hours_after_counting():
    """US-11 checklist 2: the countdown starts at counted_at."""
    assert f.feedback_closes_at(COUNTED) == datetime(2026, 10, 31, 22, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "elapsed,is_open",
    [
        (timedelta(0), True),
        (timedelta(hours=23, minutes=59), True),
        (timedelta(hours=23, minutes=59, seconds=59), True),
        (timedelta(hours=24), False),
        (timedelta(hours=24, minutes=1), False),
    ],
    ids=["right after counting", "23 h 59 min", "23 h 59 min 59 s", "exactly 24 h 0 min", "24 h 1 min"],
)
def test_answer_window(elapsed, is_open):
    """US-11 Scenario Outline: 24 години на відповідь; checklist 3: after 24 h 0 min no answer."""
    assert f.feedback_open(COUNTED, COUNTED + elapsed) is is_open


def test_uncounted_game_has_no_window():
    """US-07 checklist 6: if the game is not counted, «Зіграємо ще?» never opens."""
    assert f.feedback_open(None, COUNTED) is False


@pytest.mark.parametrize(
    "olena,maksym,allowed",
    [
        (["duo", "dating"], ["friends", "dating"], True),
        (["duo", "dating"], ["duo"], False),
        (["duo"], ["dating"], False),
        (["duo"], ["duo"], False),
    ],
    ids=["on | on | available", "on | off | unavailable", "off | on | unavailable", "off | off | unavailable"],
)
def test_closer_depends_on_dating_in_both(olena, maksym, allowed):
    """US-11 Scenario Outline: «Ближче» залежить від «Побачення» в обох (BR-13)."""
    assert f.closer_allowed(olena, maksym) is allowed
    assert f.closer_allowed(maksym, olena) is allowed, "the rule is symmetric"


def test_closer_not_allowed_with_empty_modes():
    """US-03 checklist 2: a fresh account has dating off."""
    assert f.closer_allowed([], ["dating"]) is False


@pytest.mark.parametrize(
    "mine,theirs",
    [(F.closer, F.no), (F.no, F.closer), (F.no, F.no), (F.again, F.again)],
    ids=["closer + no", "no + closer", "no + no", "again + again"],
)
def test_no_match_without_mutual_closer(mine, theirs):
    """US-12 Scenario Outline: Метч за комбінацією відповідей — rows not covered by test_matching.py (BR-14)."""
    assert m.match_after_feedback(mine, theirs) is False
