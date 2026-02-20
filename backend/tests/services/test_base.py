"""Tests for the BaseClient HTTP client."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.base import BaseClient


class ConcreteClient(BaseClient):
    """Test subclass that overrides _build_url to add /api/ prefix."""

    service_name = "test-service"

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api/{endpoint}"


@pytest.fixture
def client():
    return ConcreteClient(
        base_url="http://localhost:8989",
        retry_base_delay=0.01,
    )


class TestBaseClient:
    @respx.mock
    async def test_get_success(self, client: ConcreteClient) -> None:
        """Mock 200 response, verify returned JSON."""
        route = respx.get("http://localhost:8989/api/series").mock(
            return_value=httpx.Response(200, json={"id": 1, "title": "Test"})
        )

        result = await client.get("series")

        assert result == {"id": 1, "title": "Test"}
        assert route.called

        await client.close()

    @respx.mock
    async def test_retry_on_connect_error(self, client: ConcreteClient) -> None:
        """First call fails ConnectError, second succeeds."""
        route = respx.get("http://localhost:8989/api/series").mock(
            side_effect=[
                httpx.ConnectError("Connection refused"),
                httpx.Response(200, json={"ok": True}),
            ]
        )

        result = await client.get("series")

        assert result == {"ok": True}
        assert route.call_count == 2

        await client.close()

    @respx.mock
    async def test_raises_after_max_retries(self, client: ConcreteClient) -> None:
        """All retries fail, raises ConnectError."""
        respx.get("http://localhost:8989/api/series").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(httpx.ConnectError):
            await client.get("series")

        await client.close()

    @respx.mock
    async def test_test_connection_success(self, client: ConcreteClient) -> None:
        """Mock system/status 200, verify returns True."""
        respx.get("http://localhost:8989/api/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )

        result = await client.test_connection()

        assert result is True

        await client.close()

    @respx.mock
    async def test_test_connection_failure(self, client: ConcreteClient) -> None:
        """Mock ConnectError on system/status, verify returns False."""
        respx.get("http://localhost:8989/api/system/status").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await client.test_connection()

        assert result is False

        await client.close()
