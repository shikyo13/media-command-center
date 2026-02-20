"""WebSocket connection hub — broadcasts real-time data to all clients."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ConnectionHub:
    """Manages WebSocket connections and broadcasts messages to all clients.

    Also stores the latest snapshot per message type so REST endpoints can
    serve the most recent data without waiting for the next poll cycle.
    """

    def __init__(self) -> None:
        self.connections: list[Any] = []
        self._snapshots: dict[str, dict[str, Any]] = {}

    def connect(self, ws: Any) -> None:
        """Register a new WebSocket connection."""
        self.connections.append(ws)

    def disconnect(self, ws: Any) -> None:
        """Remove a WebSocket connection."""
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, msg_type: str, data: Any) -> None:
        """Send a JSON message to every connected client.

        Message format::

            {"type": msg_type, "timestamp": ISO8601, "data": data}

        Dead connections (those that raise on ``send_text``) are silently
        removed from the connection list.
        """
        message = {
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        self._snapshots[msg_type] = message

        payload = json.dumps(message)
        dead: list[Any] = []
        for ws in self.connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.connections.remove(ws)
            logger.warning("Removed dead WebSocket connection during broadcast")

    def get_snapshot(self, msg_type: str) -> dict[str, Any] | None:
        """Return the last broadcast message for *msg_type*, or ``None``."""
        return self._snapshots.get(msg_type)
