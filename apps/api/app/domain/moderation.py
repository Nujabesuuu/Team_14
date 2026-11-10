"""Pure rules for reports and moderator decisions (US-09, US-10). No I/O, no ORM.

Report lifecycle:
    new --(moderator)--> dismissed | warned | banned
A decision is final; only `banned` has an automatic consequence for the account.
"""

import uuid
from collections.abc import Iterable

from app.models.enums import ReportStatus


def shares_context(reporter_id: uuid.UUID, reported_id: uuid.UUID, member_ids: Iterable[uuid.UUID]) -> bool:
    """Both people took part in the reported event, conversation or match."""
    members = set(member_ids)
    return reporter_id in members and reported_id in members


def can_report(
    reporter_id: uuid.UUID, reported_id: uuid.UUID, *, shared_context: bool, already_open: bool
) -> str | None:
    """Return an error code if the report must be refused, otherwise None."""
    if reporter_id == reported_id:
        return "CANNOT_REPORT_SELF"
    if not shared_context:
        return "REPORT_CONTEXT_INVALID"
    if already_open:
        return "ALREADY_REPORTED"
    return None


def is_party(user_id: uuid.UUID, *, reporter_id: uuid.UUID, reported_id: uuid.UUID) -> bool:
    return user_id in (reporter_id, reported_id)


def can_decide(current: ReportStatus, *, involved: bool) -> str | None:
    """`involved`: the moderator wrote this report or it is about them. Nobody judges their own case."""
    if involved:
        return "REPORT_CONFLICT_OF_INTEREST"
    return None if current == ReportStatus.new else "REPORT_ALREADY_DECIDED"


def locks_account(decision: ReportStatus) -> bool:
    return decision == ReportStatus.banned
