import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import ReportContext, ReportReason, ReportStatus
from app.schemas.common import PublicUser


class ReportCreate(BaseModel):
    reported_id: uuid.UUID
    context: ReportContext
    context_id: uuid.UUID
    reason: ReportReason
    comment: str | None = Field(default=None, max_length=500)


class MyReportOut(BaseModel):
    """What the reporter sees. Deliberately has no reporter field: nobody else may get this object."""

    id: uuid.UUID
    reported: PublicUser
    context: ReportContext
    reason: ReportReason
    status: ReportStatus
    created_at: datetime
    decided_at: datetime | None

    @classmethod
    def from_report(cls, report) -> "MyReportOut":
        return cls(
            id=report.id,
            reported=PublicUser.from_user(report.reported),
            context=report.context,
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            decided_at=report.decided_at,
        )


def _person(user) -> PublicUser:
    """Name, age and mask are enough to decide a report; the photo stays with the reveal rules."""
    return PublicUser.from_user(user).model_copy(update={"photo_url": None})


class ModerationReportOut(BaseModel):
    """The moderator's view: the only place where the reporter is named."""

    id: uuid.UUID
    reporter: PublicUser
    reported: PublicUser
    context: ReportContext
    context_id: uuid.UUID
    context_label: str
    reason: ReportReason
    comment: str | None
    status: ReportStatus
    created_at: datetime
    decided_at: datetime | None
    moderator: PublicUser | None

    @classmethod
    def from_report(cls, report, context_label: str) -> "ModerationReportOut":
        return cls(
            id=report.id,
            reporter=_person(report.reporter),
            reported=_person(report.reported),
            context=report.context,
            context_id=report.context_id,
            context_label=context_label,
            reason=report.reason,
            comment=report.comment,
            status=report.status,
            created_at=report.created_at,
            decided_at=report.decided_at,
            moderator=_person(report.moderator) if report.moderator else None,
        )


class DecisionIn(BaseModel):
    # `new` is not a decision, so it is not accepted here.
    decision: Literal[ReportStatus.dismissed, ReportStatus.warned, ReportStatus.banned]
