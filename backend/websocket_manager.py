"""
backend/websocket_manager.py

Thread-safe WebSocket connection manager for live simulation telemetry broadcasting.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts traffic updates."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts and registers a new WebSocket client."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Removes a disconnected WebSocket client."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Sends data payload to all connected clients, pruning stale connections."""
        payload_str = json.dumps(data)
        stale: List[WebSocket] = []

        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(payload_str)
            except Exception:
                stale.append(connection)

        if stale:
            async with self._lock:
                for s in stale:
                    if s in self.active_connections:
                        self.active_connections.remove(s)


ws_manager = WebSocketManager()
