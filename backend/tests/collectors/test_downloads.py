"""Tests for the DownloadsCollector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.downloads import DownloadsCollector
from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


class TestDownloadsCollector:
    async def test_collect_sabnzbd_queue(self, hub: ConnectionHub) -> None:
        """SABnzbd queue data is parsed into the expected shape."""
        sabnzbd = AsyncMock()
        sabnzbd.get_queue = AsyncMock(return_value={
            "queue": {
                "speed": "10.5 MB/s",
                "sizeleft": "1.2 GB",
                "timeleft": "00:05:30",
                "slots": [
                    {
                        "filename": "Movie.2024.mkv",
                        "percentage": "45",
                        "sizeleft": "800 MB",
                        "status": "Downloading",
                        "timeleft": "00:03:00",
                    }
                ],
            }
        })

        sonarr = AsyncMock()
        sonarr.get_queue = AsyncMock(return_value={
            "records": [
                {"title": "Show S01E01", "status": "downloading", "sizeleft": 500, "size": 1000}
            ]
        })

        collector = DownloadsCollector(
            hub=hub,
            clients={"sabnzbd": sabnzbd, "sonarr": sonarr},
            interval=5.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("downloads")
        assert snapshot is not None
        data = snapshot["data"]

        # SABnzbd
        assert data["sabnzbd"]["speed"] == "10.5 MB/s"
        assert data["sabnzbd"]["timeleft"] == "00:05:30"
        assert len(data["sabnzbd"]["items"]) == 1
        assert data["sabnzbd"]["items"][0]["name"] == "Movie.2024.mkv"
        assert data["sabnzbd"]["items"][0]["percentage"] == "45"

        # Sonarr
        assert len(data["sonarr_queue"]) == 1
        assert data["sonarr_queue"][0]["title"] == "Show S01E01"

        # Radarr not configured — empty list
        assert data["radarr_queue"] == []

    async def test_collect_missing_services(self, hub: ConnectionHub) -> None:
        """When no services are configured, returns empty defaults."""
        collector = DownloadsCollector(
            hub=hub,
            clients={},
            interval=5.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("downloads")
        assert snapshot is not None
        data = snapshot["data"]

        assert data["sabnzbd"]["speed"] == ""
        assert data["sabnzbd"]["items"] == []
        assert data["sonarr_queue"] == []
        assert data["radarr_queue"] == []
