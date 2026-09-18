import uuid

from pydantic import BaseModel

from app.models.enums import FeedbackAnswer
from app.schemas.common import PublicUser


class FeedbackIn(BaseModel):
    to_user_id: uuid.UUID
    answer: FeedbackAnswer


class FeedbackResult(BaseModel):
    match_created: bool
    match_id: uuid.UUID | None = None


class PendingFeedbackOut(BaseModel):
    pending: list[PublicUser]
    done: list[uuid.UUID]
