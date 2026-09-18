import uuid

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UuidPk


class Conversation(UuidPk, Timestamped, Base):
    __tablename__ = "conversations"

    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("matches.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    match: Mapped["Match"] = relationship(back_populates="conversation", lazy="selectin")  # noqa: F821


class Message(UuidPk, Timestamped, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
