import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.domain.compatibility import GameDna
from app.models import Game, Mode, Profile, ProfileGame, User
from app.schemas.profile import MeOut, ProfileGameOut, ProfileOut, ProfileUpdate

ALLOWED_PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        bio=profile.bio,
        avatar_key=profile.avatar_key,
        accent_color=profile.accent_color,
        photo_url=profile.photo_url,
        modes=list(profile.modes),
        role=profile.role,
        playstyle=profile.playstyle,
        comms=profile.comms,
        schedule=list(profile.schedule),
        toxicity_tolerance=profile.toxicity_tolerance,
        timezone=profile.timezone,
        games=[
            ProfileGameOut(id=pg.game.id, name=pg.game.name, slug=pg.game.slug, rank=pg.rank) for pg in profile.games
        ],
        onboarded=profile.onboarded,
    )


def me_out(user: User) -> MeOut:
    return MeOut(user=user, profile=profile_out(user.profile))


def dna_of(profile: Profile) -> GameDna:
    return GameDna(
        games=frozenset(pg.game.slug for pg in profile.games),
        role=profile.role,
        playstyle=profile.playstyle,
        comms=profile.comms,
        schedule=frozenset(profile.schedule),
        toxicity=profile.toxicity_tolerance,
    )


async def update_profile(session: AsyncSession, user: User, data: ProfileUpdate) -> User:
    profile = user.profile
    profile_was_onboarded = profile.onboarded
    patch = data.model_dump(exclude_unset=True)

    if "display_name" in patch:
        user.display_name = patch.pop("display_name").strip()

    if "modes" in patch:
        modes = [m.value for m in patch.pop("modes")]
        if Mode.dating in modes and user.age < 18:
            raise ApiError(422, "DATING_REQUIRES_18", "Dating mode is available from 18 years old")
        profile.modes = modes

    if "games" in patch:
        wanted = patch.pop("games")
        ids = [g["game_id"] for g in wanted]
        found = {g.id: g for g in (await session.scalars(select(Game).where(Game.id.in_(ids)))).all()}
        missing = [str(i) for i in ids if i not in found]
        if missing:
            raise ApiError(422, "UNKNOWN_GAME", f"Unknown game ids: {', '.join(missing)}")
        profile.games = [ProfileGame(game_id=g["game_id"], rank=g.get("rank")) for g in wanted]

    for key, value in patch.items():
        setattr(profile, key, value)

    was_onboarded = profile_was_onboarded
    await session.commit()
    await session.refresh(user)

    if user.profile.onboarded and not was_onboarded:
        # First time the profile is complete: pair with the demo guide so chat works right away.
        from app.services.bot import ensure_guide_match

        await ensure_guide_match(session, user)
    return user


async def save_photo(session: AsyncSession, user: User, file: UploadFile) -> str:
    ext = ALLOWED_PHOTO_TYPES.get(file.content_type or "")
    if ext is None:
        raise ApiError(422, "UNSUPPORTED_PHOTO", "Use JPEG, PNG or WebP")
    content = await file.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise ApiError(422, "PHOTO_TOO_LARGE", "Photo must be under 5 MB")

    media = Path(get_settings().media_dir)
    media.mkdir(parents=True, exist_ok=True)
    name = f"{user.id}-{uuid.uuid4().hex[:8]}{ext}"
    (media / name).write_bytes(content)

    user.profile.photo_url = f"/media/{name}"
    await session.commit()
    return user.profile.photo_url


async def set_premium(session: AsyncSession, user: User, enabled: bool) -> User:
    user.is_premium = enabled
    await session.commit()
    return user
