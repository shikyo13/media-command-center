"""Tests for the HealthCollector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.health import HealthCollector
from app.ws.hub import ConnectionHub


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


class TestHealthCollector:
    async def test_collect_all_healthy(self, hub: ConnectionHub) -> None:
        """All services return status; broadcast contains online entries."""
        sonarr = AsyncMock()
        sonarr.get_system_status = AsyncMock(
            return_value={"version": "4.0.0"}
        )
        radarr = AsyncMock()
        radarr.get_system_status = AsyncMock(
            return_value={"version": "5.1.0"}
        )

        collector = HealthCollector(
            hub=hub,
            clients={"sonarr": sonarr, "radarr": radarr},
            interval=10.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("health")
        assert snapshot is not None

        services = snapshot["data"]["services"]
        assert len(services) == 2

        by_name = {s["name"]: s for s in services}
        assert by_name["sonarr"]["status"] == "online"
        assert by_name["sonarr"]["version"] == "4.0.0"
        assert isinstance(by_name["sonarr"]["response_ms"], int)

        assert by_name["radarr"]["status"] == "online"
        assert by_name["radarr"]["version"] == "5.1.0"

    async def test_collect_service_offline(self, hub: ConnectionHub) -> None:
        """A service that raises is reported as offline."""
        sonarr = AsyncMock()
        sonarr.get_system_status = AsyncMock(
            return_value={"version": "4.0.0"}
        )
        plex = AsyncMock()
        plex.get_system_status = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        collector = HealthCollector(
            hub=hub,
            clients={"sonarr": sonarr, "plex": plex},
            interval=10.0,
        )
        await collector.collect()

        snapshot = hub.get_snapshot("health")
        services = snapshot["data"]["services"]
        by_name = {s["name"]: s for s in services}

        assert by_name["sonarr"]["status"] == "online"
        assert by_name["plex"]["status"] == "offline"
        assert by_name["plex"]["version"] == ""
