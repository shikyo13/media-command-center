"""Tests for the StreamingCollector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.streaming import StreamingCollector
from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


class TestStreamingCollector:
    async def test_collect_sessions(self, hub: ConnectionHub) -> None:
        """Sessions are parsed correctly, transcode count computed."""
        plex = AsyncMock()
        plex.get_sessions = AsyncMock(return_value=[
            {
                "User": {"title": "alice"},
                "title": "Pilot",
                "grandparentTitle": "Breaking Bad",
                "parentIndex": 1,
                "index": 1,
                "Media": [{"Part": [{"decision": "directplay"}]}],
            },
            {
                "User": {"title": "bob"},
                "title": "Ozymandias",
                "grandparentTitle": "Breaking Bad",
                "parentIndex": 5,
                "index": 14,
                "Media": [{"Part": [{"decision": "transcode"}]}],
                "TranscodeSession": {"videoDecision": "transcode"},
            },
        ])

        collector = StreamingCollector(
            hub=hub,
            clients={"plex": plex},
            interval=5.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("streaming")
        assert snapshot is not None
        data = snapshot["data"]

        assert data["stream_count"] == 2
        assert data["transcode_count"] == 1

        sessions = data["sessions"]
        assert len(sessions) == 2

        assert sessions[0]["user"] == "alice"
        assert sessions[0]["title"] == "Pilot"
        assert sessions[0]["decision"] == "directplay"
        assert sessions[0]["grandparentTitle"] == "Breaking Bad"
        assert sessions[0]["parentIndex"] == 1

        assert sessions[1]["user"] == "bob"
        assert sessions[1]["decision"] == "transcode"

    async def test_no_plex(self, hub: ConnectionHub) -> None:
        """When Plex is not configured, broadcast empty data."""
        collector = StreamingCollector(
            hub=hub,
            clients={},
            interval=5.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("streaming")
        assert snapshot is not None
        data = snapshot["data"]

        assert data["stream_count"] == 0
        assert data["transcode_count"] == 0
        assert data["sessions"] == []
