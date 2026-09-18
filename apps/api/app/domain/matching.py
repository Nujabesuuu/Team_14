"""Pure rules for how two people become a match."""

from app.models.enums import FeedbackAnswer, Mode, SwipeDirection

ADULT_AGE = 18


def match_after_feedback(mine: FeedbackAnswer, theirs: FeedbackAnswer | None) -> bool:
    """A match happens only when *both* players chose 'closer'. Answers stay private otherwise."""
    return mine == FeedbackAnswer.closer and theirs == FeedbackAnswer.closer


def match_after_swipe(mine: SwipeDirection, theirs: SwipeDirection | None) -> bool:
    return mine == SwipeDirection.right and theirs == SwipeDirection.right


def can_swipe_right(is_premium: bool, rights_today: int, limit: int) -> str | None:
    if is_premium:
        return None
    return "SWIPE_LIMIT" if rights_today >= limit else None


def rights_left(is_premium: bool, rights_today: int, limit: int) -> int | None:
    """None means unlimited."""
    if is_premium:
        return None
    return max(0, limit - rights_today)


def share_mode(a_modes: list[str], b_modes: list[str]) -> bool:
    return bool(set(a_modes) & set(b_modes))


def can_see_in_mode(mode: Mode, viewer_age: int, target_modes: list[str], target_age: int) -> bool:
    """Discover feed rule: both must have the mode; dating additionally requires both adults."""
    if mode not in target_modes:
        return False
    if mode == Mode.dating:
        return viewer_age >= ADULT_AGE and target_age >= ADULT_AGE
    return True
