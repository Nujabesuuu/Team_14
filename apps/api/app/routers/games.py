from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import Session
from app.models import Game
from app.schemas.profile import GameOut

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=list[GameOut])
async def list_games(session: Session) -> list[Game]:
    return list((await session.scalars(select(Game).order_by(Game.name))).all())
