import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser, Session
from app.schemas.match import MessageOut
from app.services import chat as service

router = APIRouter(prefix="/conversations", tags=["chat"])


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def messages(
    conversation_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
    before: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[MessageOut]:
    conv = await service.get_conversation_for(session, conversation_id, user.id)
    return await service.history(session, conv, before=before, limit=limit)


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def send(conversation_id: uuid.UUID, data: MessageIn, user: CurrentUser, session: Session) -> MessageOut:
    """HTTP fallback for sending; the WebSocket path is preferred by the client."""
    conv = await service.get_conversation_for(session, conversation_id, user.id)
    return await service.send_message(session, conv, user.id, data.body)
