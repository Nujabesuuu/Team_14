from fastapi import APIRouter

from app.core.deps import CurrentUser, Session, require_premium
from app.models import Mode
from app.schemas.discover import DiscoverCard, DiscoverOut
from app.services import discover as service

router = APIRouter(tags=["discover"])


@router.get("/discover", response_model=DiscoverOut)
async def discover(user: CurrentUser, session: Session, mode: Mode = Mode.duo) -> DiscoverOut:
    return await service.discover(session, user, mode)


@router.get("/likes/incoming", response_model=list[DiscoverCard])
async def incoming_likes(user: CurrentUser, session: Session) -> list[DiscoverCard]:
    require_premium(user)
    return await service.incoming_likes(session, user)
