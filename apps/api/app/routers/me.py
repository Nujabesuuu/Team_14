from fastapi import APIRouter, UploadFile

from app.core.deps import CurrentUser, Session
from app.schemas.profile import MeOut, PhotoOut, PremiumToggle, ProfileUpdate
from app.services import profile as service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(user: CurrentUser) -> MeOut:
    return service.me_out(user)


@router.put("", response_model=MeOut)
async def update_me(data: ProfileUpdate, user: CurrentUser, session: Session) -> MeOut:
    return service.me_out(await service.update_profile(session, user, data))


@router.post("/photo", response_model=PhotoOut)
async def upload_photo(file: UploadFile, user: CurrentUser, session: Session) -> PhotoOut:
    return PhotoOut(photo_url=await service.save_photo(session, user, file))


@router.post("/premium", response_model=MeOut)
async def toggle_premium(data: PremiumToggle, user: CurrentUser, session: Session) -> MeOut:
    """Dev-only stand-in for a payment provider: flips Teamate+ on or off."""
    return service.me_out(await service.set_premium(session, user, data.enabled))
