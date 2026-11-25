import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """A naive datetime is taken as UTC; an aware one is converted to UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class UtcDateTime(TypeDecorator):
    """`timestamptz` that is always UTC-aware in Python, on SQLite too.

    SQLite has no time zone type: it drops the offset on write and returns naive values on read.
    Without this, "+02:00" input was stored as wall-clock time, JSON went out without a zone (the
    client read it as local time, G-10), and comparing with `utcnow()` raised TypeError.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return None if value is None else as_utc(value)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return None if value is None else as_utc(value)


class UuidPk:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, nullable=False)
