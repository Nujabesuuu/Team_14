from app.domain import reveal as d


def test_match_unlocks_stage_one():
    assert d.stage_after_match() == 1


def test_shared_event_never_regresses():
    assert d.stage_after_shared_event(1) == 2
    assert d.stage_after_shared_event(3) == 3


def test_clear_only_with_both_consents():
    assert d.stage_after_consent(1, True, False) == 1
    assert d.stage_after_consent(2, False, True) == 2
    assert d.stage_after_consent(1, True, True) == 3


def test_blur_pixels():
    assert [d.blur_px(s) for s in d.STAGES] == [24, 12, 4, 0]
    assert d.blur_px(99) == 24
