"""Sonarr API client — /api/v3/, X-Api-Key header."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class SonarrClient(BaseClient):
    """HTTP client for the Sonarr v3 API."""

    service_name = "sonarr"

    def __init__(self, base_url: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api/v3/{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self._api_key,
            "Accept": "application/json",
        }

    # -- Sonarr-specific endpoints ------------------------------------------

    async def get_system_status(self) -> Any:
        """GET system/status."""
        return await self.get("system/status")

    async def get_queue(self, page: int = 1, page_size: int = 50) -> Any:
        """GET queue with pagination."""
        return await self.get(
            "queue",
            params={"page": page, "pageSize": page_size},
        )

    async def get_calendar(
        self, start: str | None = None, end: str | None = None
    ) -> Any:
        """GET calendar with optional date range."""
        params: dict[str, Any] = {"includeSeries": "true"}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        return await self.get("calendar", params=params)
