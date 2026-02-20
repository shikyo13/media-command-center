"""Tests for Arr service clients (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.prowlarr import ProwlarrClient
from app.services.bazarr import BazarrClient
from app.services.overseerr import OverseerrClient


# ---------------------------------------------------------------------------
# Sonarr
# ---------------------------------------------------------------------------

class TestSonarrClient:
    @pytest.fixture
    def client(self):
        return SonarrClient(
            base_url="http://localhost:8989",
            api_key="test-sonarr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_get_queue(self, client: SonarrClient) -> None:
        route = respx.get("http://localhost:8989/api/v3/queue").mock(
            return_value=httpx.Response(
                200,
                json={"page": 1, "records": []},
            )
        )

        result = await client.get_queue(page=1, page_size=20)

        assert result == {"page": 1, "records": []}
        assert route.called
        # Verify query params were sent
        request = route.calls[0].request
        assert request.url.params["page"] == "1"
        assert request.url.params["pageSize"] == "20"

        await client.close()

    @respx.mock
    async def test_get_calendar(self, client: SonarrClient) -> None:
        route = respx.get("http://localhost:8989/api/v3/calendar").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )

        result = await client.get_calendar(start="2026-01-01", end="2026-01-31")

        assert result == [{"id": 1}]
        assert route.called
        request = route.calls[0].request
        assert request.url.params["start"] == "2026-01-01"
        assert request.url.params["end"] == "2026-01-31"

        await client.close()

    @respx.mock
    async def test_headers_include_api_key(self, client: SonarrClient) -> None:
        route = respx.get("http://localhost:8989/api/v3/system/status").mock(
            return_value=httpx.Response(200, json={"version": "4.0"})
        )

        await client.get_system_status()

        request = route.calls[0].request
        assert request.headers["X-Api-Key"] == "test-sonarr-key"
        assert request.headers["Accept"] == "application/json"

        await client.close()


# ---------------------------------------------------------------------------
# Radarr
# ---------------------------------------------------------------------------

class TestRadarrClient:
    @pytest.fixture
    def client(self):
        return RadarrClient(
            base_url="http://localhost:7878",
            api_key="test-radarr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_get_queue(self, client: RadarrClient) -> None:
        route = respx.get("http://localhost:7878/api/v3/queue").mock(
            return_value=httpx.Response(
                200,
                json={"page": 1, "records": []},
            )
        )

        result = await client.get_queue(page=2, page_size=10)

        assert result == {"page": 1, "records": []}
        request = route.calls[0].request
        assert request.url.params["page"] == "2"
        assert request.url.params["pageSize"] == "10"

        await client.close()

    @respx.mock
    async def test_get_calendar(self, client: RadarrClient) -> None:
        route = respx.get("http://localhost:7878/api/v3/calendar").mock(
            return_value=httpx.Response(200, json=[{"id": 42}])
        )

        result = await client.get_calendar()

        assert result == [{"id": 42}]
        assert route.called
        # No start/end params when omitted
        request = route.calls[0].request
        assert "start" not in request.url.params
        assert "end" not in request.url.params

        await client.close()


# ---------------------------------------------------------------------------
# Prowlarr
# ---------------------------------------------------------------------------

class TestProwlarrClient:
    @pytest.fixture
    def client(self):
        return ProwlarrClient(
            base_url="http://localhost:9696",
            api_key="test-prowlarr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_system_status(self, client: ProwlarrClient) -> None:
        route = respx.get("http://localhost:9696/api/v1/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )

        result = await client.get_system_status()

        assert result == {"version": "1.0"}
        assert route.called
        request = route.calls[0].request
        assert request.headers["X-Api-Key"] == "test-prowlarr-key"

        await client.close()


# ---------------------------------------------------------------------------
# Bazarr
# ---------------------------------------------------------------------------

class TestBazarrClient:
    @pytest.fixture
    def client(self):
        return BazarrClient(
            base_url="http://localhost:6767",
            api_key="test-bazarr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_system_status(self, client: BazarrClient) -> None:
        route = respx.get("http://localhost:6767/api/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.2"})
        )

        result = await client.get_system_status()

        assert result == {"version": "1.2"}
        assert route.called
        request = route.calls[0].request
        # Bazarr uses X-API-KEY header
        assert request.headers["X-API-KEY"] == "test-bazarr-key"

        await client.close()


# ---------------------------------------------------------------------------
# Overseerr
# ---------------------------------------------------------------------------

class TestOverseerrClient:
    @pytest.fixture
    def client(self):
        return OverseerrClient(
            base_url="http://localhost:5055",
            api_key="test-overseerr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_system_status(self, client: OverseerrClient) -> None:
        # Overseerr status endpoint is "status", NOT "system/status"
        route = respx.get("http://localhost:5055/api/v1/status").mock(
            return_value=httpx.Response(200, json={"version": "2.0"})
        )

        result = await client.get_system_status()

        assert result == {"version": "2.0"}
        assert route.called
        request = route.calls[0].request
        assert request.headers["X-Api-Key"] == "test-overseerr-key"

        await client.close()
