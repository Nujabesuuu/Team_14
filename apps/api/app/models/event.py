import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UtcDateTime, UuidPk, utcnow
from app.models.enums import EventKind, EventStatus


class Event(UuidPk, Timestamped, Base):
    __tablename__ = "events"

    host_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("games.id"), nullable=False)
    kind: Mapped[EventKind] = mapped_column(Enum(EventKind), default=EventKind.squad, nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    max_slots: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.open, nullable=False)
    # US-07: "counted" is not a status but a filled `counted_at`, so the status enum and the client stay as they were.
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    counted_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    host: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    game: Mapped["Game"] = relationship(lazy="selectin")  # noqa: F821
    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="selectin"
    )
    confirmations: Mapped[list["GameConfirmation"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    @property
    def participant_ids(self) -> list[uuid.UUID]:
        return [p.user_id for p in self.participants]

    @property
    def confirmed_ids(self) -> list[uuid.UUID]:
        return [c.user_id for c in self.confirmations]


class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, nullable=False)

    event: Mapped[Event] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821


class GameConfirmation(Base):
    """US-07: "we really played" from one participant. The composite PK allows one per person."""

    __tablename__ = "game_confirmations"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, nullable=False)
