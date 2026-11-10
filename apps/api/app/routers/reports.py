import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.models import ReportStatus
from app.schemas.report import DecisionIn, ModerationReportOut, MyReportOut, ReportCreate
from app.services import reports as service

router = APIRouter(prefix="/reports", tags=["safety"])
moderation_router = APIRouter(prefix="/moderation/reports", tags=["moderation"])


@router.post("", response_model=MyReportOut, status_code=201)
async def create_report(data: ReportCreate, user: CurrentUser, session: Session) -> MyReportOut:
    return MyReportOut.from_report(await service.create_report(session, user, data))


@router.get("/mine", response_model=list[MyReportOut])
async def my_reports(user: CurrentUser, session: Session) -> list[MyReportOut]:
    return [MyReportOut.from_report(r) for r in await service.my_reports(session, user)]


@moderation_router.get("", response_model=list[ModerationReportOut])
async def moderation_queue(
    user: CurrentUser, session: Session, status: ReportStatus | None = None
) -> list[ModerationReportOut]:
    return await service.moderation_queue(session, user, status)


@moderation_router.post("/{report_id}/decision", response_model=ModerationReportOut)
async def decide(report_id: uuid.UUID, data: DecisionIn, user: CurrentUser, session: Session) -> ModerationReportOut:
    return await service.decide(session, user, report_id, data.decision)
