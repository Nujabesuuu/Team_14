import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import Conversation, Message
from app.schemas.match import MessageOut
from app.services.blocks import is_blocked
from app.ws.hub import hub

MAX_BODY = 2000


async def get_conversation_for(session: AsyncSession, conversation_id: uuid.UUID, viewer_id: uuid.UUID) -> Conversation:
    conv = await session.get(Conversation, conversation_id)
    if conv is None:
        raise ApiError(404, "CONVERSATION_NOT_FOUND", "Conversation not found")
    if not conv.match.involves(viewer_id):
        raise ApiError(403, "NOT_YOUR_CONVERSATION", "You are not part of this conversation")
    if await is_blocked(session, viewer_id, conv.match.other_id(viewer_id)):
        raise ApiError(403, "BLOCKED", "This conversation is closed")
    return conv


async def history(
    session: AsyncSession, conv: Conversation, *, before: datetime | None, limit: int = 50
) -> list[MessageOut]:
    q = select(Message).where(Message.conversation_id == conv.id)
    if before is not None:
        q = q.where(Message.created_at < before)
    rows = (await session.scalars(q.order_by(desc(Message.created_at)).limit(limit))).all()
    return [MessageOut.model_validate(m, from_attributes=True) for m in reversed(rows)]


async def send_message(session: AsyncSession, conv: Conversation, sender_id: uuid.UUID, body: str) -> MessageOut:
    body = body.strip()
    if not body:
        raise ApiError(422, "EMPTY_MESSAGE", "Message cannot be empty")
    if len(body) > MAX_BODY:
        raise ApiError(422, "MESSAGE_TOO_LONG", f"Message must be under {MAX_BODY} characters")
    msg = Message(conversation_id=conv.id, sender_id=sender_id, body=body)
    session.add(msg)
    await session.commit()
    out = MessageOut.model_validate(msg, from_attributes=True)
    await hub.send_to_users(
        (conv.match.user_a_id, conv.match.user_b_id),
        {"type": "message.new", "message": out.model_dump(mode="json")},
    )
    return out
