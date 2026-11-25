from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError, account_banned
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.accounts import old_enough
from app.models import Profile, User
from app.models._base import utcnow
from app.schemas.auth import LoginIn, RegisterIn


async def register(session: AsyncSession, data: RegisterIn) -> tuple[User, str]:
    # Before the email lookup, so a minor learns nothing about which addresses are registered.
    # The UTC date, like the daily like limit: date.today() followed the machine's zone, so between 00:00 and
    # 02:00 in Kyiv the same birth date passed on a laptop and failed in Docker (G-13 tracks the Kyiv day).
    if not old_enough(data.birth_date, utcnow().date()):
        raise ApiError(422, "TOO_YOUNG", "Teamate is for adults 18+")
    exists = await session.scalar(select(User.id).where(User.email == data.email.lower()))
    if exists:
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        display_name=data.display_name.strip(),
        birth_date=data.birth_date,
    )
    user.profile = Profile()
    session.add(user)
    await session.commit()
    return user, create_access_token(user.id)


async def login(session: AsyncSession, data: LoginIn) -> tuple[User, str]:
    user = await session.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "Wrong email or password")
    # After the password check, so only the owner learns that the account is banned.
    if user.is_banned:
        raise account_banned()
    return user, create_access_token(user.id)
