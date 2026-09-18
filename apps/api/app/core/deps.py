from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.models import User

_bearer = HTTPBearer(auto_error=False)

Session = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: Session,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if creds is None:
        raise ApiError(401, "UNAUTHORIZED", "Missing bearer token")
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise ApiError(401, "UNAUTHORIZED", "Invalid or expired token")
    user = await session.get(User, user_id)
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_premium(user: User) -> None:
    if not user.is_premium:
        raise ApiError(402, "PREMIUM_REQUIRED", "This feature requires Teamate+")
