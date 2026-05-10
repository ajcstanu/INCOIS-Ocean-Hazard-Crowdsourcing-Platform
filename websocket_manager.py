"""
WebSocket connection manager for real-time dashboard updates.
Broadcasts new reports and hotspot changes to connected clients.
"""

import json
from typing import Dict, Set
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        # room_name → set of WebSocket connections
        self._rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str = "dashboard") -> None:
        await websocket.accept()
        self._rooms.setdefault(room, set()).add(websocket)
        logger.info(f"WS connected | room={room} | total={len(self._rooms[room])}")

    def disconnect(self, websocket: WebSocket, room: str = "dashboard") -> None:
        if room in self._rooms:
            self._rooms[room].discard(websocket)
        logger.info(f"WS disconnected | room={room}")

    async def broadcast(self, data: dict, room: str = "dashboard") -> None:
        """Broadcast a message to all clients in a room."""
        if room not in self._rooms:
            return
        dead: Set[WebSocket] = set()
        message = json.dumps(data, default=str)
        for ws in list(self._rooms[room]):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._rooms[room].discard(ws)

    async def send_personal(self, websocket: WebSocket, data: dict) -> None:
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception:
            pass

    def room_size(self, room: str) -> int:
        return len(self._rooms.get(room, set()))


ws_manager = ConnectionManager()
