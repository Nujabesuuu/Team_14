from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Profile, User
from app.schemas.auth import LoginIn, RegisterIn


async def register(session: AsyncSession, data: RegisterIn) -> tuple[User, str]:
    exists = await session.scalar(select(User.id).where(User.email == data.email.lower()))
    if exists:
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        display_name=data.display_name.strip(),
        birth_date=data.birth_date,
    )
    if user.age < 13:
        raise ApiError(422, "TOO_YOUNG", "You must be at least 13 to use Teamate")
    user.profile = Profile()
    session.add(user)
    await session.commit()
    return user, create_access_token(user.id)


async def login(session: AsyncSession, data: LoginIn) -> tuple[User, str]:
    user = await session.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "Wrong email or password")
    return user, create_access_token(user.id)
