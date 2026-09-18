from fastapi import APIRouter

from app.core.deps import CurrentUser, Session, require_premium
from app.schemas.discover import SwipeIn, SwipeResult
from app.services import discover as service

router = APIRouter(prefix="/swipes", tags=["discover"])


@router.post("", response_model=SwipeResult)
async def swipe(data: SwipeIn, user: CurrentUser, session: Session) -> SwipeResult:
    return await service.swipe(session, user, data.to_user_id, data.direction)


@router.post("/undo", status_code=204)
async def undo(user: CurrentUser, session: Session) -> None:
    require_premium(user)
    await service.undo_last_swipe(session, user)
