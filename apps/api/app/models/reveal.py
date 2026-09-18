import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PhotoReveal(Base):
    """Per-user reveal state inside a match: how clearly *my* photo is shown to the other."""

    __tablename__ = "photo_reveals"

    match_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    stage: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    consent_next: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    early_request: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    match: Mapped["Match"] = relationship(back_populates="reveals")  # noqa: F821
