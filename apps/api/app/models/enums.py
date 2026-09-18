from enum import StrEnum


class EventStatus(StrEnum):
    open = "open"
    full = "full"
    in_progress = "in_progress"
    finished = "finished"
    cancelled = "cancelled"


class EventKind(StrEnum):
    squad = "squad"
    game_date = "game_date"


class FeedbackAnswer(StrEnum):
    again = "again"
    closer = "closer"
    no = "no"


class SwipeDirection(StrEnum):
    left = "left"
    right = "right"


class MatchSource(StrEnum):
    post_game = "post_game"
    mutual_like = "mutual_like"


class Mode(StrEnum):
    duo = "duo"
    friends = "friends"
    dating = "dating"


class Role(StrEnum):
    support = "support"
    carry = "carry"
    flex = "flex"
    tank = "tank"
    igl = "igl"


class Playstyle(StrEnum):
    casual = "casual"
    competitive = "competitive"


class Comms(StrEnum):
    voice = "voice"
    text = "text"
    both = "both"


class AvatarKey(StrEnum):
    operator = "operator"
    impostor = "impostor"
    duelist = "duelist"
    strategist = "strategist"
    vanguard = "vanguard"
    sage = "sage"
    pilot = "pilot"
    builder = "builder"
