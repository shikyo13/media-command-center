"""Tests for the CalendarCollector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.calendar import CalendarCollector
from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


class TestCalendarCollector:
    async def test_collect_episodes_and_movies(self, hub: ConnectionHub) -> None:
        """Both Sonarr and Radarr calendar data is parsed correctly."""
        sonarr = AsyncMock()
        sonarr.get_calendar = AsyncMock(return_value=[
            {
                "series": {"title": "Breaking Bad"},
                "title": "Pilot",
                "airDateUtc": "2026-02-20T02:00:00Z",
                "seasonNumber": 1,
                "episodeNumber": 1,
                "hasFile": False,
            },
            {
                "series": {"title": "Better Call Saul"},
                "title": "Uno",
                "airDateUtc": "2026-02-21T02:00:00Z",
                "seasonNumber": 1,
                "episodeNumber": 1,
                "hasFile": True,
            },
        ])

        radarr = AsyncMock()
        radarr.get_calendar = AsyncMock(return_value=[
            {
                "title": "Dune: Part Two",
                "digitalRelease": "2026-02-22",
                "hasFile": False,
            },
        ])

        collector = CalendarCollector(
            hub=hub,
            clients={"sonarr": sonarr, "radarr": radarr},
            interval=60.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("calendar")
        assert snapshot is not None
        data = snapshot["data"]

        # Episodes
        assert len(data["episodes"]) == 2
        ep = data["episodes"][0]
        assert ep["series"] == "Breaking Bad"
        assert ep["title"] == "Pilot"
        assert ep["airDate"] == "2026-02-20T02:00:00Z"
        assert ep["season"] == 1
        assert ep["episode"] == 1
        assert ep["hasFile"] is False

        assert data["episodes"][1]["hasFile"] is True

        # Movies
        assert len(data["movies"]) == 1
        assert data["movies"][0]["title"] == "Dune: Part Two"
        assert data["movies"][0]["releaseDate"] == "2026-02-22"
        assert data["movies"][0]["hasFile"] is False

    async def test_collect_no_services(self, hub: ConnectionHub) -> None:
        """When no services are configured, broadcast empty lists."""
        collector = CalendarCollector(
            hub=hub,
            clients={},
            interval=60.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("calendar")
        assert snapshot is not None
        data = snapshot["data"]

        assert data["episodes"] == []
        assert data["movies"] == []
