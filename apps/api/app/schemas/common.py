import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvatarKey


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PublicUser(OrmModel):
    """What other users may see about someone. Never includes email or birth date."""

    id: uuid.UUID
    display_name: str
    age: int
    avatar_key: AvatarKey
    accent_color: str
    photo_url: str | None = None
    is_premium: bool = False

    @classmethod
    def from_user(cls, user) -> "PublicUser":
        p = user.profile
        return cls(
            id=user.id,
            display_name=user.display_name,
            age=user.age,
            avatar_key=p.avatar_key,
            accent_color=p.accent_color,
            photo_url=p.photo_url,
            is_premium=user.is_premium,
        )
