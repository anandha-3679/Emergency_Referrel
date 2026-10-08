"""
WebSocket and Event Notification Hub.
Supports:
- Real-time WebSockets to role rooms (e.g., /ws/dispatcher/all, /ws/hospital/{id}, /ws/crew/{case_id})
- Broadcast to all connected clients
- Event log backup for polling clients
"""

from typing import Dict, List, Any
import json
import asyncio
from fastapi import WebSocket
from app.store import store


class ConnectionManager:
    def __init__(self):
        # Maps channel key (e.g. "dispatcher:all", "hospital:hosp-victoria", "crew:case-123") -> set of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        async with self.lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str):
        async with self.lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]

    async def broadcast_channel(self, channel: str, message: Dict[str, Any]):
        """Sends message to all connections in a specific channel."""
        connections = self.active_connections.get(channel, [])
        dead_conns = []
        payload_str = json.dumps(message)
        for ws in connections:
            try:
                await ws.send_text(payload_str)
            except Exception:
                dead_conns.append(ws)

        if dead_conns:
            async with self.lock:
                for ws in dead_conns:
                    if channel in self.active_connections and ws in self.active_connections[channel]:
                        self.active_connections[channel].remove(ws)

    async def broadcast_event(self, event_type: str, payload: Dict[str, Any], target_hospital_id: str = None, case_id: str = None):
        """
        Record in store event log, then broadcast across relevant channels:
        - dispatcher:all
        - hospital:{target_hospital_id} (if applicable)
        - crew:{case_id} (if applicable)
        - global (all)
        """
        event = store.add_event(event_type, payload)

        msg = {
            "type": event_type,
            "payload": payload,
            "timestamp": event["timestamp"],
        }

        # 1. Dispatcher always gets everything
        await self.broadcast_channel("dispatcher:all", msg)

        # 2. Target hospital channel if specified
        if target_hospital_id:
            await self.broadcast_channel(f"hospital:{target_hospital_id}", msg)

        # 3. Case channel if specified
        if case_id:
            await self.broadcast_channel(f"crew:{case_id}", msg)

        # 4. Broadcast to general channel
        await self.broadcast_channel("all", msg)


manager = ConnectionManager()
