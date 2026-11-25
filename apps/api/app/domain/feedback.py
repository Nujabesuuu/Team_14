"""Pure rules for the secret "Play again?" answer (US-11) that runs after a counted game."""

from datetime import datetime, timedelta

from app.models.enums import Mode

FEEDBACK_WINDOW = timedelta(hours=24)


def feedback_closes_at(counted_at: datetime) -> datetime:
    return counted_at + FEEDBACK_WINDOW


def feedback_open(counted_at: datetime | None, now: datetime) -> bool:
    """BR-12: the window opens when the game is counted; at exactly 24 h 0 min it is already closed."""
    return counted_at is not None and now < feedback_closes_at(counted_at)


def closer_allowed(my_modes: list[str], their_modes: list[str]) -> bool:
    """BR-13: "closer" exists only when *both* opted into dating, so nobody is courted against their settings."""
    return Mode.dating in my_modes and Mode.dating in their_modes
