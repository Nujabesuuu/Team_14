import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UuidPk
from app.models.enums import ReportContext, ReportReason, ReportStatus


class Report(UuidPk, Timestamped, Base):
    """A complaint in the manual moderation queue together with the moderator's decision on it."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("reporter_id <> reported_id", name="ck_report_not_self"),
        # One undecided report per reporter, person and place; decided ones may repeat.
        Index(
            "uq_report_open_case",
            "reporter_id",
            "reported_id",
            "context",
            "context_id",
            unique=True,
            sqlite_where=text("status = 'new'"),
            postgresql_where=text("status = 'new'"),
        ),
    )

    reporter_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    context: Mapped[ReportContext] = mapped_column(Enum(ReportContext), nullable=False)
    # Event, conversation or match id depending on `context`, so it cannot be a foreign key.
    context_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    reason: Mapped[ReportReason] = mapped_column(Enum(ReportReason), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.new, nullable=False, index=True
    )
    moderator_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reporter: Mapped["User"] = relationship(foreign_keys=[reporter_id], lazy="selectin")  # noqa: F821
    reported: Mapped["User"] = relationship(foreign_keys=[reported_id], lazy="selectin")  # noqa: F821
    moderator: Mapped["User | None"] = relationship(foreign_keys=[moderator_id], lazy="selectin")  # noqa: F821
