"""Tests for the WebSocket ConnectionHub."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


def _make_ws() -> AsyncMock:
    """Create a mock WebSocket with an async send_text method."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestConnectionHub:
    async def test_connect_disconnect(self, hub: ConnectionHub) -> None:
        """Verify the connections list grows on connect and shrinks on disconnect."""
        ws1 = _make_ws()
        ws2 = _make_ws()

        hub.connect(ws1)
        assert len(hub.connections) == 1

        hub.connect(ws2)
        assert len(hub.connections) == 2

        hub.disconnect(ws1)
        assert len(hub.connections) == 1
        assert hub.connections[0] is ws2

        hub.disconnect(ws2)
        assert len(hub.connections) == 0

    async def test_broadcast(self, hub: ConnectionHub) -> None:
        """Verify both connections receive message with correct structure."""
        ws1 = _make_ws()
        ws2 = _make_ws()
        hub.connect(ws1)
        hub.connect(ws2)

        await hub.broadcast("health", {"services": []})

        # Both websockets should have received the message
        assert ws1.send_text.call_count == 1
        assert ws2.send_text.call_count == 1

        # Verify message structure
        payload = json.loads(ws1.send_text.call_args[0][0])
        assert payload["type"] == "health"
        assert "timestamp" in payload
        assert payload["data"] == {"services": []}

    async def test_broadcast_removes_dead_connections(
        self, hub: ConnectionHub
    ) -> None:
        """Dead ws (raises on send_text) gets removed from connections."""
        alive_ws = _make_ws()
        dead_ws = _make_ws()
        dead_ws.send_text.side_effect = Exception("Connection closed")

        hub.connect(alive_ws)
        hub.connect(dead_ws)
        assert len(hub.connections) == 2

        await hub.broadcast("health", {"services": []})

        # Dead connection should be removed
        assert len(hub.connections) == 1
        assert hub.connections[0] is alive_ws

        # Alive connection should have received the message
        assert alive_ws.send_text.call_count == 1

    async def test_get_snapshot(self, hub: ConnectionHub) -> None:
        """After broadcast, snapshot returns the data."""
        await hub.broadcast("health", {"services": ["sonarr"]})

        snapshot = hub.get_snapshot("health")
        assert snapshot is not None
        assert snapshot["type"] == "health"
        assert snapshot["data"] == {"services": ["sonarr"]}
        assert "timestamp" in snapshot

    async def test_get_snapshot_missing(self, hub: ConnectionHub) -> None:
        """Returns None for unknown type."""
        result = hub.get_snapshot("nonexistent")
        assert result is None
