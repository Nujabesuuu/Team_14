import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.schemas.match import MatchOut
from app.services import matches as matches_service
from app.services import reveal as service

router = APIRouter(prefix="/matches/{match_id}/reveal", tags=["reveal"])


@router.post("/consent", response_model=MatchOut)
async def consent(match_id: uuid.UUID, user: CurrentUser, session: Session) -> MatchOut:
    match = await matches_service.get_match_for(session, match_id, user.id)
    return await matches_service.match_out(session, await service.consent(session, match, user), user)


@router.post("/early-request", response_model=MatchOut)
async def early_request(match_id: uuid.UUID, user: CurrentUser, session: Session) -> MatchOut:
    match = await matches_service.get_match_for(session, match_id, user.id)
    return await matches_service.match_out(session, await service.early_request(session, match, user), user)


@router.post("/early-accept", response_model=MatchOut)
async def early_accept(match_id: uuid.UUID, user: CurrentUser, session: Session) -> MatchOut:
    match = await matches_service.get_match_for(session, match_id, user.id)
    return await matches_service.match_out(session, await service.early_accept(session, match, user), user)
