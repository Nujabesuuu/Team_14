import uuid

from pydantic import BaseModel

from app.models.enums import Comms, Mode, Playstyle, Role, SwipeDirection
from app.schemas.common import PublicUser
from app.schemas.profile import ProfileGameOut


class DiscoverCard(BaseModel):
    user: PublicUser
    bio: str
    modes: list[Mode]
    role: Role | None
    playstyle: Playstyle | None
    comms: Comms | None
    schedule: list[str]
    games: list[ProfileGameOut]
    compatibility: int


class DiscoverOut(BaseModel):
    cards: list[DiscoverCard]
    rights_left: int | None


class SwipeIn(BaseModel):
    to_user_id: uuid.UUID
    direction: SwipeDirection


class SwipeResult(BaseModel):
    match_created: bool
    match_id: uuid.UUID | None = None
    rights_left: int | None


class BlockIn(BaseModel):
    user_id: uuid.UUID
