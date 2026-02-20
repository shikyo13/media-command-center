"""SABnzbd API client — single /api endpoint, query-param based."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class SABnzbdClient(BaseClient):
    """HTTP client for the SABnzbd API.

    SABnzbd routes **all** operations through a single ``/api`` endpoint;
    the ``mode`` query parameter selects the action.
    """

    service_name = "sabnzbd"

    def __init__(self, base_url: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        """Always resolve to ``/api`` regardless of *endpoint*."""
        return f"{self._base_url}/api"

    async def _api(self, mode: str, **params: Any) -> Any:
        """Execute a SABnzbd API call for the given *mode*."""
        query: dict[str, Any] = {
            "mode": mode,
            "apikey": self._api_key,
            "output": "json",
            **params,
        }
        return await self.get("", params=query)

    # -- Health check --------------------------------------------------------

    async def test_connection(self) -> bool:
        """Verify connectivity by requesting the SABnzbd version."""
        try:
            await self._api("version")
            return True
        except Exception:
            return False

    # -- SABnzbd-specific endpoints ------------------------------------------

    async def get_system_status(self) -> Any:
        """Version check (fullstatus was removed in SABnzbd 4.x)."""
        return await self._api("version")

    async def get_queue(self) -> Any:
        """Current download queue."""
        return await self._api("queue")

    async def get_version(self) -> Any:
        """SABnzbd version string."""
        return await self._api("version")
