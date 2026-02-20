"""Tests for custom service clients (Plex, SABnzbd, Tdarr)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.plex import PlexClient
from app.services.sabnzbd import SABnzbdClient
from app.services.tdarr import TdarrClient


# ---------------------------------------------------------------------------
# Plex
# ---------------------------------------------------------------------------

class TestPlexClient:
    @pytest.fixture
    def client(self):
        return PlexClient(
            base_url="http://localhost:32400",
            token="test-plex-token",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_get_sessions(self, client: PlexClient) -> None:
        """get_sessions returns the Metadata list from MediaContainer."""
        payload = {
            "MediaContainer": {
                "size": 2,
                "Metadata": [
                    {"title": "Movie A", "Player": {"state": "playing"}},
                    {"title": "Movie B", "Player": {"state": "paused"}},
                ],
            }
        }
        route = respx.get("http://localhost:32400/status/sessions").mock(
            return_value=httpx.Response(200, json=payload)
        )

        result = await client.get_sessions()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Movie A"
        assert result[1]["title"] == "Movie B"
        assert route.called

        await client.close()

    @respx.mock
    async def test_token_in_headers_and_params(self, client: PlexClient) -> None:
        """Plex token must appear in both the X-Plex-Token header and query params."""
        route = respx.get("http://localhost:32400/identity").mock(
            return_value=httpx.Response(
                200, json={"MediaContainer": {"machineIdentifier": "abc123"}}
            )
        )

        await client.get_system_status()

        request = route.calls[0].request
        # Token in header
        assert request.headers["X-Plex-Token"] == "test-plex-token"
        # Token in query params
        assert request.url.params["X-Plex-Token"] == "test-plex-token"

        await client.close()


# ---------------------------------------------------------------------------
# SABnzbd
# ---------------------------------------------------------------------------

class TestSABnzbdClient:
    @pytest.fixture
    def client(self):
        return SABnzbdClient(
            base_url="http://localhost:8080",
            api_key="test-sab-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_get_queue(self, client: SABnzbdClient) -> None:
        """get_queue returns the queue payload from the single /api endpoint."""
        payload = {"queue": {"slots": [{"nzo_id": "SABnzbd_1"}]}}
        route = respx.get("http://localhost:8080/api").mock(
            return_value=httpx.Response(200, json=payload)
        )

        result = await client.get_queue()

        assert result == payload
        assert route.called
        request = route.calls[0].request
        assert request.url.params["mode"] == "queue"

        await client.close()

    @respx.mock
    async def test_api_key_in_params(self, client: SABnzbdClient) -> None:
        """Every SABnzbd call must include apikey and output=json in query params."""
        route = respx.get("http://localhost:8080/api").mock(
            return_value=httpx.Response(200, json={"version": "4.0"})
        )

        await client.get_version()

        request = route.calls[0].request
        assert request.url.params["apikey"] == "test-sab-key"
        assert request.url.params["output"] == "json"
        assert request.url.params["mode"] == "version"

        await client.close()


# ---------------------------------------------------------------------------
# Tdarr
# ---------------------------------------------------------------------------

class TestTdarrClient:
    @pytest.fixture
    def client(self):
        return TdarrClient(
            base_url="http://localhost:8265",
            api_key="test-tdarr-key",
            retry_base_delay=0.01,
        )

    @respx.mock
    async def test_get_status(self, client: TdarrClient) -> None:
        """GET /api/v2/status returns the Tdarr status payload."""
        payload = {"nodes": 2, "queue": 5}
        route = respx.get("http://localhost:8265/api/v2/status").mock(
            return_value=httpx.Response(200, json=payload)
        )

        result = await client.get_status()

        assert result == payload
        assert route.called
        request = route.calls[0].request
        assert request.headers["x-api-key"] == "test-tdarr-key"

        await client.close()

    @respx.mock
    async def test_get_staged_files(self, client: TdarrClient) -> None:
        """POST /api/v2/cruddb with StagedJSONDB collection."""
        payload = [{"_id": "file1"}, {"_id": "file2"}]
        route = respx.post("http://localhost:8265/api/v2/cruddb").mock(
            return_value=httpx.Response(200, json=payload)
        )

        result = await client.get_staged_files()

        assert result == payload
        assert route.called
        # Verify the POST body contains the correct cruddb payload
        import json
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "data": {"collection": "StagedJSONDB", "mode": "getAll"}
        }

        await client.close()


