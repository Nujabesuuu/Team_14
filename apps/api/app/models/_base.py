import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class UuidPk:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
