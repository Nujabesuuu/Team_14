from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import Timestamped, UuidPk
from app.models.enums import UserRole


class User(UuidPk, Timestamped, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Scripted demo companion (Teamate Guide): auto-matches, replies in chat, agrees to reveal.
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Moderators are appointed by the team (seed); no endpoint changes the role.
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    # Set by a moderator's "banned" decision; a banned account is refused on login and on every request.
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["Profile"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    def age_on(self, today: date) -> int:
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    @property
    def age(self) -> int:
        return self.age_on(date.today())

    @property
    def is_moderator(self) -> bool:
        return self.role == UserRole.moderator

    @property
    def is_banned(self) -> bool:
        return self.banned_at is not None
