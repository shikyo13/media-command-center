"""Overseerr API client — /api/v1/, X-Api-Key header, status endpoint differs."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class OverseerrClient(BaseClient):
    """HTTP client for the Overseerr v1 API.

    Key difference: the status endpoint is ``status``, not ``system/status``.
    """

    service_name = "overseerr"

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

    # -- Overseerr-specific endpoints ---------------------------------------

    async def get_system_status(self) -> Any:
        """GET status (not system/status)."""
        return await self.get("status")
