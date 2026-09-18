"""Pure rules for gradual photo reveal.

Stages are per user: `stage` is how clearly *my* photo is shown to my match.
    0 - stranger: heavy blur + grayscale (default before any match)
    1 - matched: medium blur (set automatically when the match is created)
    2 - played together after matching: light blur
    3 - both consented: clear photo
"""

STAGES = (0, 1, 2, 3)
STRANGER, MATCHED, PLAYED, CLEAR = STAGES

_BLUR = {STRANGER: 24, MATCHED: 12, PLAYED: 4, CLEAR: 0}


def stage_after_match() -> int:
    return MATCHED


def stage_after_shared_event(current: int) -> int:
    """Never regress a stage; a shared finished event unlocks at least PLAYED."""
    return max(current, PLAYED)


def stage_after_consent(current: int, my_consent: bool, their_consent: bool) -> int:
    return CLEAR if (my_consent and their_consent) else current


def blur_px(stage: int) -> int:
    return _BLUR.get(stage, _BLUR[STRANGER])
