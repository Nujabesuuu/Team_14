import uuid

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import AvatarKey, Comms, Playstyle, Role


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    avatar_key: Mapped[AvatarKey] = mapped_column(Enum(AvatarKey), default=AvatarKey.raven, nullable=False)
    accent_color: Mapped[str] = mapped_column(String(7), default="#E60012", nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Game DNA
    modes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    role: Mapped[Role | None] = mapped_column(Enum(Role), nullable=True)
    playstyle: Mapped[Playstyle | None] = mapped_column(Enum(Playstyle), nullable=True)
    comms: Mapped[Comms | None] = mapped_column(Enum(Comms), nullable=True)
    schedule: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    toxicity_tolerance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Kyiv", nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")  # noqa: F821
    games: Mapped[list["ProfileGame"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def onboarded(self) -> bool:
        return bool(self.modes) and self.role is not None and len(self.games) > 0


class ProfileGame(Base):
    __tablename__ = "profile_games"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    game_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    rank: Mapped[str | None] = mapped_column(String(40), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="games")
    game: Mapped["Game"] = relationship(lazy="selectin")  # noqa: F821
