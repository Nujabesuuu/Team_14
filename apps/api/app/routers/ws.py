import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.db import SessionLocal
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.services import chat as chat_service
from app.ws.hub import hub

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str) -> None:
    user_id = decode_access_token(token)
    if user_id is None:
        await ws.close(code=4401)
        return

    await hub.connect(user_id, ws)
    try:
        while True:
            payload = await ws.receive_json()
            await _handle(user_id, payload, ws)
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(user_id, ws)


async def _handle(user_id: uuid.UUID, payload: dict, ws: WebSocket) -> None:
    kind = payload.get("type")
    if kind == "ping":
        await ws.send_json({"type": "pong"})
        return
    if kind != "message.send":
        await ws.send_json({"type": "error", "code": "UNKNOWN_TYPE", "detail": f"Unknown type {kind!r}"})
        return
    try:
        conversation_id = uuid.UUID(str(payload.get("conversation_id")))
    except ValueError:
        await ws.send_json({"type": "error", "code": "BAD_CONVERSATION_ID", "detail": "Invalid conversation id"})
        return
    async with SessionLocal() as session:
        try:
            conv = await chat_service.get_conversation_for(session, conversation_id, user_id)
            await chat_service.send_message(session, conv, user_id, str(payload.get("body", "")))
        except ApiError as exc:
            await ws.send_json({"type": "error", "code": exc.code, "detail": exc.detail})
