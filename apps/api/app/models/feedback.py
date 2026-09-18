import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import Timestamped, UuidPk
from app.models.enums import FeedbackAnswer


class PostGameFeedback(UuidPk, Timestamped, Base):
    __tablename__ = "post_game_feedback"
    __table_args__ = (UniqueConstraint("event_id", "from_user_id", "to_user_id", name="uq_feedback_pair"),)

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    from_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    answer: Mapped[FeedbackAnswer] = mapped_column(Enum(FeedbackAnswer), nullable=False)
