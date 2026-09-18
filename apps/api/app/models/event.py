import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UuidPk, utcnow
from app.models.enums import EventKind, EventStatus


class Event(UuidPk, Timestamped, Base):
    __tablename__ = "events"

    host_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("games.id"), nullable=False)
    kind: Mapped[EventKind] = mapped_column(Enum(EventKind), default=EventKind.squad, nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_slots: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.open, nullable=False)

    host: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    game: Mapped["Game"] = relationship(lazy="selectin")  # noqa: F821
    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def participant_ids(self) -> list[uuid.UUID]:
        return [p.user_id for p in self.participants]


class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    event: Mapped[Event] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
