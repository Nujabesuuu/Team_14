import uuid

from pydantic import BaseModel, Field

from app.models.enums import AvatarKey, Comms, Mode, Playstyle, Role
from app.schemas.auth import AccountOut
from app.schemas.common import OrmModel


class GameOut(OrmModel):
    id: uuid.UUID
    name: str
    slug: str
    is_chill: bool
    cover_color: str


class ProfileGameIn(BaseModel):
    game_id: uuid.UUID
    rank: str | None = Field(default=None, max_length=40)


class ProfileGameOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    rank: str | None = None


class ProfileOut(BaseModel):
    bio: str
    avatar_key: AvatarKey
    accent_color: str
    photo_url: str | None
    modes: list[Mode]
    role: Role | None
    playstyle: Playstyle | None
    comms: Comms | None
    schedule: list[str]
    toxicity_tolerance: int
    timezone: str
    games: list[ProfileGameOut]
    onboarded: bool


class ProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=300)
    avatar_key: AvatarKey | None = None
    accent_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    modes: list[Mode] | None = None
    role: Role | None = None
    playstyle: Playstyle | None = None
    comms: Comms | None = None
    schedule: list[str] | None = None
    toxicity_tolerance: int | None = Field(default=None, ge=1, le=5)
    timezone: str | None = Field(default=None, max_length=64)
    games: list[ProfileGameIn] | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=40)


class MeOut(BaseModel):
    user: AccountOut
    profile: ProfileOut


class PremiumToggle(BaseModel):
    enabled: bool


class PhotoOut(BaseModel):
    photo_url: str
