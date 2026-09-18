import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import Timestamped, UuidPk
from app.models.enums import SwipeDirection


class Swipe(UuidPk, Timestamped, Base):
    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_swipe_pair"),)

    from_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[SwipeDirection] = mapped_column(Enum(SwipeDirection), nullable=False)
