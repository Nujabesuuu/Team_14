from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidPk


class Game(UuidPk, Base):
    __tablename__ = "games"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    # "Chill" games are calm/cooperative and allowed for Game Date events.
    is_chill: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cover_color: Mapped[str] = mapped_column(String(7), default="#2A2A2A", nullable=False)
