import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UuidPk
from app.models.enums import MatchSource


def canonical_pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """Order a pair of user ids so (a, b) and (b, a) map to the same row."""
    return (a, b) if a.int < b.int else (b, a)


class Match(UuidPk, Timestamped, Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_match_pair"),)

    user_a_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[MatchSource] = mapped_column(Enum(MatchSource), nullable=False)

    user_a: Mapped["User"] = relationship(foreign_keys=[user_a_id], lazy="selectin")  # noqa: F821
    user_b: Mapped["User"] = relationship(foreign_keys=[user_b_id], lazy="selectin")  # noqa: F821
    reveals: Mapped[list["PhotoReveal"]] = relationship(  # noqa: F821
        back_populates="match", cascade="all, delete-orphan", lazy="selectin"
    )
    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        back_populates="match", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    def involves(self, user_id: uuid.UUID) -> bool:
        return user_id in (self.user_a_id, self.user_b_id)

    def other_id(self, user_id: uuid.UUID) -> uuid.UUID:
        return self.user_b_id if user_id == self.user_a_id else self.user_a_id

    def reveal_for(self, user_id: uuid.UUID) -> "PhotoReveal":  # noqa: F821
        return next(r for r in self.reveals if r.user_id == user_id)
