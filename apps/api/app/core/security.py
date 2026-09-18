import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expires = datetime.now(UTC) + timedelta(days=settings.jwt_expires_days)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
