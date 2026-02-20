"""Prowlarr API client — /api/v1/, X-Api-Key header."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class ProwlarrClient(BaseClient):
    """HTTP client for the Prowlarr v1 API."""

    service_name = "prowlarr"

    def __init__(self, base_url: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api/v1/{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self._api_key,
            "Accept": "application/json",
        }

    # -- Prowlarr-specific endpoints ----------------------------------------

    async def get_system_status(self) -> Any:
        """GET system/status."""
        return await self.get("system/status")
