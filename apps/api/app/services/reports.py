import logging
import uuid

from sqlalchemy import desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.domain import moderation as rules
from app.models import Conversation, Event, EventStatus, Match, Report, ReportContext, ReportStatus, User
from app.models._base import utcnow
from app.schemas.report import ModerationReportOut, ReportCreate
from app.services.events import broadcast
from app.ws.hub import BANNED_CLOSE_CODE, hub

logger = logging.getLogger(__name__)

_ERRORS = {
    "CANNOT_REPORT_SELF": (422, "You cannot report yourself"),
    # One message for "no such event/chat/person" and "you were not there": nothing to probe.
    "REPORT_CONTEXT_INVALID": (422, "You can only report someone you played or matched with"),
    "ALREADY_REPORTED": (409, "You already reported this person here. The team is looking into it."),
    "REPORT_ALREADY_DECIDED": (409, "This report already has a decision"),
    "REPORT_CONFLICT_OF_INTEREST": (403, "You are part of this report. Another moderator has to decide it."),
}


def _raise(code: str) -> None:
    status, detail = _ERRORS[code]
    raise ApiError(status, code, detail)


def require_moderator(user: User) -> None:
    if not user.is_moderator:
        raise ApiError(403, "MODERATOR_ONLY", "Only moderators can do this")


async def _context_member_ids(session: AsyncSession, context: ReportContext, context_id: uuid.UUID) -> set[uuid.UUID]:
    """Everyone who took part in the reported event, conversation or match. Empty if it does not exist."""
    if context == ReportContext.event:
        event = await session.get(Event, context_id)
        return set(event.participant_ids) if event else set()
    if context == ReportContext.chat:
        conversation = await session.get(Conversation, context_id)
        match = conversation.match if conversation else None
    else:
        match = await session.get(Match, context_id)
    return {match.user_a_id, match.user_b_id} if match else set()


async def create_report(session: AsyncSession, reporter: User, data: ReportCreate) -> Report:
    members = await _context_member_ids(session, data.context, data.context_id)
    open_report = await session.scalar(
        select(Report.id).where(
            Report.reporter_id == reporter.id,
            Report.reported_id == data.reported_id,
            Report.context == data.context,
            Report.context_id == data.context_id,
            Report.status == ReportStatus.new,
        )
    )
    error = rules.can_report(
        reporter.id,
        data.reported_id,
        shared_context=rules.shares_context(reporter.id, data.reported_id, members),
        already_open=open_report is not None,
    )
    if error:
        _raise(error)

    report = Report(
        reporter_id=reporter.id,
        reported_id=data.reported_id,
        context=data.context,
        context_id=data.context_id,
        reason=data.reason,
        comment=(data.comment or "").strip() or None,
    )
    session.add(report)
    try:
        await session.commit()
    except IntegrityError:
        # A double tap passed the check above twice; the unique index let only one through.
        await session.rollback()
        _raise("ALREADY_REPORTED")
    await session.refresh(report)
    return report


async def my_reports(session: AsyncSession, reporter: User) -> list[Report]:
    return list(
        (
            await session.scalars(
                select(Report).where(Report.reporter_id == reporter.id).order_by(desc(Report.created_at))
            )
        ).all()
    )


async def _event_labels(session: AsyncSession, reports: list[Report]) -> dict[uuid.UUID, str]:
    ids = {r.context_id for r in reports if r.context == ReportContext.event}
    if not ids:
        return {}
    events = (await session.scalars(select(Event).where(Event.id.in_(ids)))).all()
    return {e.id: f"{e.game.name} · {e.title}" for e in events}


def _context_label(report: Report, event_labels: dict[uuid.UUID, str]) -> str:
    """Tells the moderator where it happened without opening anything else."""
    if report.context == ReportContext.event:
        return event_labels.get(report.context_id, "Deleted event")
    if report.context == ReportContext.chat:
        return f"Chat between {report.reporter.display_name} and {report.reported.display_name}"
    return f"Photo of {report.reported.display_name}"


async def _moderation_out(session: AsyncSession, reports: list[Report]) -> list[ModerationReportOut]:
    labels = await _event_labels(session, reports)
    return [ModerationReportOut.from_report(r, _context_label(r, labels)) for r in reports]


async def moderation_queue(
    session: AsyncSession, moderator: User, status: ReportStatus | None
) -> list[ModerationReportOut]:
    require_moderator(moderator)
    q = select(Report).order_by(desc(Report.created_at))
    if status is not None:
        q = q.where(Report.status == status)
    return await _moderation_out(session, list((await session.scalars(q)).all()))


async def decide(
    session: AsyncSession, moderator: User, report_id: uuid.UUID, decision: ReportStatus
) -> ModerationReportOut:
    # Role first: a regular player must not learn which report ids exist.
    require_moderator(moderator)
    report = await session.get(Report, report_id)
    if report is None:
        raise ApiError(404, "REPORT_NOT_FOUND", "Report not found")
    involved = rules.is_party(moderator.id, reporter_id=report.reporter_id, reported_id=report.reported_id)
    error = rules.can_decide(report.status, involved=involved)
    if error:
        _raise(error)

    # Conditional update: if two moderators press at once, exactly one decision wins.
    result = await session.execute(
        update(Report)
        .where(Report.id == report.id, Report.status == ReportStatus.new)
        .values(status=decision, moderator_id=moderator.id, decided_at=utcnow())
    )
    if result.rowcount != 1:
        await session.rollback()
        _raise("REPORT_ALREADY_DECIDED")

    changed_events: list[Event] = []
    if rules.locks_account(decision):
        changed_events = await _lock_out(session, report.reported)
    await session.commit()
    await session.refresh(report)

    if rules.locks_account(decision):
        await _announce_lock_out(session, report.reported_id, changed_events)
    return (await _moderation_out(session, [report]))[0]


async def _announce_lock_out(session: AsyncSession, user_id: uuid.UUID, changed_events: list[Event]) -> None:
    """Best effort: the decision is already committed, a failed push must not turn it into a 500."""
    try:
        await hub.close_user(user_id, BANNED_CLOSE_CODE)
        for event in changed_events:
            await broadcast(session, event)
    except Exception:  # noqa: BLE001 - clients re-read the state on their next request anyway
        logger.exception("Could not push the ban of %s to open sockets", user_id)


async def _lock_out(session: AsyncSession, user: User) -> list[Event]:
    """Ban the account and take it out of every game that has not started yet.

    Finished and running events are left alone: they are the evidence behind reports.
    """
    if user.banned_at is None:
        # A second "banned" decision keeps the moment of the first ban.
        user.banned_at = utcnow()
    upcoming = (
        await session.scalars(
            select(Event).where(
                Event.status.in_([EventStatus.open, EventStatus.full]),
                Event.participants.any(user_id=user.id),
            )
        )
    ).all()
    for event in upcoming:
        if event.host_id == user.id:
            event.status = EventStatus.cancelled
        else:
            event.participants = [p for p in event.participants if p.user_id != user.id]
            event.status = EventStatus.open
    return list(upcoming)
