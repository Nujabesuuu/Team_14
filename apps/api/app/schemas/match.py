import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import MatchSource
from app.schemas.common import PublicUser


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime


class RevealState(BaseModel):
    my_stage: int
    their_stage: int
    my_consent: bool
    their_consent: bool
    early_request_from_me: bool
    early_request_from_them: bool


class MatchOut(BaseModel):
    id: uuid.UUID
    other: PublicUser
    source: MatchSource
    conversation_id: uuid.UUID
    reveal: RevealState
    compatibility: int
    last_message: MessageOut | None = None
    created_at: datetime
