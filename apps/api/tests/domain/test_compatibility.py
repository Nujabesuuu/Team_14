from app.domain.compatibility import GameDna, score

FULL = GameDna(
    games=frozenset({"valorant", "dota2"}),
    role="support",
    playstyle="casual",
    comms="voice",
    schedule=frozenset({"evening", "weekend"}),
    toxicity=2,
)


def test_identical_dna_is_100():
    twin = GameDna(**{**FULL.__dict__, "role": "carry"})  # support + carry = complementary
    assert score(FULL, twin) == 100


def test_disjoint_dna_is_low():
    stranger = GameDna(
        games=frozenset({"minecraft"}),
        role="flex",
        playstyle="competitive",
        comms="text",
        schedule=frozenset({"morning"}),
        toxicity=5,
    )
    # only role partial (25% of 10) survives, toxicity distance 3 gives 2.5 points
    assert score(FULL, stranger) == 5


def test_role_complement_beats_same_role():
    same = GameDna(role="support")
    complement = GameDna(role="carry")
    assert score(GameDna(role="support"), complement) > score(GameDna(role="support"), same)


def test_score_is_symmetric_and_bounded():
    a, b = FULL, GameDna(games=frozenset({"valorant"}), comms="both", toxicity=4)
    assert score(a, b) == score(b, a)
    assert 0 <= score(a, b) <= 100
