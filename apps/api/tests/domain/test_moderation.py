import uuid

from app.domain import moderation as d
from app.models.enums import ReportStatus as S

A, B, C = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def test_shared_context_needs_both_people():
    assert d.shares_context(A, B, [A, B, C]) is True
    assert d.shares_context(A, B, [A, C]) is False
    assert d.shares_context(A, B, [B]) is False
    assert d.shares_context(A, B, []) is False


def test_cannot_report_yourself():
    assert d.can_report(A, A, shared_context=True, already_open=False) == "CANNOT_REPORT_SELF"


def test_report_needs_a_shared_context():
    assert d.can_report(A, B, shared_context=False, already_open=False) == "REPORT_CONTEXT_INVALID"


def test_one_open_report_per_person_and_context():
    assert d.can_report(A, B, shared_context=True, already_open=True) == "ALREADY_REPORTED"
    assert d.can_report(A, B, shared_context=True, already_open=False) is None


def test_a_report_is_decided_once():
    assert d.can_decide(S.new, involved=False) is None
    for decided in (S.dismissed, S.warned, S.banned):
        assert d.can_decide(decided, involved=False) == "REPORT_ALREADY_DECIDED"


def test_a_moderator_does_not_judge_their_own_case():
    assert d.is_party(A, reporter_id=A, reported_id=B) is True
    assert d.is_party(B, reporter_id=A, reported_id=B) is True
    assert d.is_party(C, reporter_id=A, reported_id=B) is False
    assert d.can_decide(S.new, involved=True) == "REPORT_CONFLICT_OF_INTEREST"


def test_only_the_ban_decision_locks_the_account():
    assert d.locks_account(S.banned) is True
    assert d.locks_account(S.warned) is False
    assert d.locks_account(S.dismissed) is False
