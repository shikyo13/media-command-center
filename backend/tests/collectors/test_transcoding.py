"""Tests for the TranscodingCollector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.transcoding import TranscodingCollector
from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


class TestTranscodingCollector:
    async def test_collect(self, hub: ConnectionHub) -> None:
        """Tdarr data is parsed into nodes, queue, and statistics."""
        tdarr = AsyncMock()
        tdarr.get_nodes = AsyncMock(return_value={
            "node1": {
                "nodeName": "Server-Node",
                "workers": {"transcoderWorkers": 2},
            },
        })
        tdarr.get_staged_files = AsyncMock(return_value=[
            {"_id": "file1"},
            {"_id": "file2"},
            {"_id": "file3"},
        ])
        tdarr.get_statistics = AsyncMock(return_value={
            "totalFileCount": 1500,
            "totalTranscodeCount": 800,
            "sizeDiff": -5000000,
        })

        collector = TranscodingCollector(
            hub=hub,
            clients={"tdarr": tdarr},
            interval=15.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("transcoding")
        assert snapshot is not None
        data = snapshot["data"]

        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "node1"
        assert data["nodes"][0]["name"] == "Server-Node"
        assert data["nodes"][0]["workers"] == {"transcoderWorkers": 2}

        assert data["queue_size"] == 3
        assert data["total_files"] == 1500
        assert data["total_transcodes"] == 800
        assert data["size_diff_bytes"] == -5000000

    async def test_no_tdarr(self, hub: ConnectionHub) -> None:
        """When Tdarr is not configured, broadcast empty defaults."""
        collector = TranscodingCollector(
            hub=hub,
            clients={},
            interval=15.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("transcoding")
        assert snapshot is not None
        data = snapshot["data"]

        assert data["nodes"] == []
        assert data["queue_size"] == 0
        assert data["total_files"] == 0
        assert data["total_transcodes"] == 0
        assert data["size_diff_bytes"] == 0
