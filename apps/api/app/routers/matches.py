import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.schemas.match import MatchOut
from app.services import matches as service

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
async def list_matches(user: CurrentUser, session: Session) -> list[MatchOut]:
    return await service.list_matches(session, user)


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: uuid.UUID, user: CurrentUser, session: Session) -> MatchOut:
    match = await service.get_match_for(session, match_id, user.id)
    return await service.match_out(session, match, user)
