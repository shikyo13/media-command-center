"""Bazarr API client — /api/ (no version), 'X-API-KEY' header."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class BazarrClient(BaseClient):
    """HTTP client for the Bazarr API.

    Key differences from other *arr clients:
    - URL prefix is ``/api/`` (no version segment).
    - Auth header is ``X-API-KEY``.
    """

    service_name = "bazarr"

    def __init__(self, base_url: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api/{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self._api_key,
            "Accept": "application/json",
        }

    # -- Bazarr-specific endpoints ------------------------------------------

    async def get_system_status(self) -> Any:
        """GET system/status."""
        return await self.get("system/status")
