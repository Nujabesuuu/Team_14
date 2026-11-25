import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.feedback import feedback_closes_at
from app.models.enums import EventKind, EventStatus
from app.schemas.common import PublicUser
from app.schemas.profile import GameOut


class EventCreate(BaseModel):
    game_id: uuid.UUID
    kind: EventKind = EventKind.squad
    title: str = Field(min_length=3, max_length=80)
    starts_at: datetime
    max_slots: int = Field(default=2, ge=2, le=10)


class EventOut(BaseModel):
    id: uuid.UUID
    host: PublicUser
    game: GameOut
    kind: EventKind
    title: str
    starts_at: datetime
    max_slots: int
    status: EventStatus
    participants: list[PublicUser]
    is_host: bool
    is_participant: bool
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    counted_at: datetime | None
    confirmations: int
    confirmed_by_me: bool
    feedback_closes_at: datetime | None

    @classmethod
    def from_event(cls, event, viewer_id: uuid.UUID) -> "EventOut":
        return cls(
            id=event.id,
            host=PublicUser.from_user(event.host),
            game=GameOut.model_validate(event.game),
            kind=event.kind,
            title=event.title,
            starts_at=event.starts_at,
            max_slots=event.max_slots,
            status=event.status,
            participants=[PublicUser.from_user(p.user) for p in event.participants],
            is_host=event.host_id == viewer_id,
            is_participant=viewer_id in event.participant_ids,
            created_at=event.created_at,
            started_at=event.started_at,
            finished_at=event.finished_at,
            counted_at=event.counted_at,
            confirmations=len(event.confirmations),
            confirmed_by_me=viewer_id in event.confirmed_ids,
            feedback_closes_at=feedback_closes_at(event.counted_at) if event.counted_at else None,
        )
