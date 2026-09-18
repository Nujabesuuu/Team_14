from app.domain import matching as d
from app.models.enums import FeedbackAnswer as F
from app.models.enums import Mode
from app.models.enums import SwipeDirection as S


def test_match_requires_both_closer():
    assert d.match_after_feedback(F.closer, F.closer) is True
    assert d.match_after_feedback(F.closer, F.again) is False
    assert d.match_after_feedback(F.again, F.closer) is False
    assert d.match_after_feedback(F.closer, None) is False


def test_match_requires_both_right_swipes():
    assert d.match_after_swipe(S.right, S.right) is True
    assert d.match_after_swipe(S.right, S.left) is False
    assert d.match_after_swipe(S.right, None) is False


def test_free_swipe_limit():
    assert d.can_swipe_right(False, 19, 20) is None
    assert d.can_swipe_right(False, 20, 20) == "SWIPE_LIMIT"
    assert d.can_swipe_right(True, 999, 20) is None
    assert d.rights_left(False, 5, 20) == 15
    assert d.rights_left(True, 5, 20) is None


def test_share_mode():
    assert d.share_mode(["duo"], ["duo", "dating"]) is True
    assert d.share_mode(["duo"], ["dating"]) is False


def test_dating_visibility_requires_adults():
    assert d.can_see_in_mode(Mode.dating, 20, ["dating"], 20) is True
    assert d.can_see_in_mode(Mode.dating, 17, ["dating"], 20) is False
    assert d.can_see_in_mode(Mode.dating, 20, ["dating"], 17) is False
    assert d.can_see_in_mode(Mode.duo, 15, ["duo"], 15) is True
    assert d.can_see_in_mode(Mode.duo, 15, ["friends"], 15) is False
