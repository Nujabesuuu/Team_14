"""Deterministic Game DNA compatibility score (0-100).

Weights (sum = 100):
    shared games ......... up to 35
    playstyle match ...... 15
    comms match .......... 10
    schedule overlap ..... up to 20
    toxicity closeness ... up to 10
    role complement ...... up to 10
"""

from dataclasses import dataclass, field

W_GAMES, W_PLAYSTYLE, W_COMMS, W_SCHEDULE, W_TOXICITY, W_ROLE = 35, 15, 10, 20, 10, 10

# Pairs of roles that play well together get the full role bonus.
_COMPLEMENTARY = {frozenset({"support", "carry"}), frozenset({"tank", "carry"}), frozenset({"igl", "flex"})}


@dataclass(frozen=True)
class GameDna:
    games: frozenset[str] = field(default_factory=frozenset)
    role: str | None = None
    playstyle: str | None = None
    comms: str | None = None
    schedule: frozenset[str] = field(default_factory=frozenset)
    toxicity: int = 3  # 1 (zero tolerance) .. 5 (anything goes)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _comms_score(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.0
    if a == b or "both" in (a, b):
        return 1.0
    return 0.0


def _role_score(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.0
    if frozenset({a, b}) in _COMPLEMENTARY:
        return 1.0
    if a == b:
        return 0.5
    return 0.25


def score(a: GameDna, b: GameDna) -> int:
    total = 0.0
    total += W_GAMES * _jaccard(a.games, b.games)
    total += W_PLAYSTYLE * (1.0 if a.playstyle and a.playstyle == b.playstyle else 0.0)
    total += W_COMMS * _comms_score(a.comms, b.comms)
    total += W_SCHEDULE * _jaccard(a.schedule, b.schedule)
    total += W_TOXICITY * (1 - abs(a.toxicity - b.toxicity) / 4)
    total += W_ROLE * _role_score(a.role, b.role)
    return max(0, min(100, round(total)))
