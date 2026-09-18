from fastapi import APIRouter

from app.core.deps import CurrentUser, Session
from app.schemas.discover import BlockIn
from app.services import blocks as service

router = APIRouter(prefix="/blocks", tags=["safety"])


@router.post("", status_code=204)
async def block(data: BlockIn, user: CurrentUser, session: Session) -> None:
    await service.block_user(session, user.id, data.user_id)
