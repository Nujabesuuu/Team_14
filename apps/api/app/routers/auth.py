from fastapi import APIRouter

from app.core.deps import Session
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(data: RegisterIn, session: Session) -> TokenOut:
    user, token = await service.register(session, data)
    return TokenOut(access_token=token, user=user)


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, session: Session) -> TokenOut:
    user, token = await service.login(session, data)
    return TokenOut(access_token=token, user=user)
