"""In-memory WebSocket hub. One process only — see docs/adr/0004 for the scaling path."""

import uuid
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket


class ConnectionHub:
    def __init__(self) -> None:
        self._sockets: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._sockets[user_id].add(ws)

    def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        self._sockets[user_id].discard(ws)
        if not self._sockets[user_id]:
            self._sockets.pop(user_id, None)

    def is_online(self, user_id: uuid.UUID) -> bool:
        return bool(self._sockets.get(user_id))

    async def send_to_user(self, user_id: uuid.UUID, payload: dict[str, Any]) -> None:
        for ws in list(self._sockets.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 - a dead socket must not break the request
                self.disconnect(user_id, ws)

    async def send_to_users(self, user_ids: Iterable[uuid.UUID], payload: dict[str, Any]) -> None:
        for uid in set(user_ids):
            await self.send_to_user(uid, payload)


hub = ConnectionHub()
