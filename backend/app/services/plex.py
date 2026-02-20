"""Plex Media Server API client — token in both headers and query params."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class PlexClient(BaseClient):
    """HTTP client for the Plex Media Server API.

    Plex requires the auth token in **both** the ``X-Plex-Token`` header
    and as a query parameter on every request.
    """

    service_name = "plex"

    def __init__(self, base_url: str, token: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._token = token

    def _get_headers(self) -> dict[str, str]:
        return {"X-Plex-Token": self._token, "Accept": "application/json"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """Inject the Plex token into query params before delegating."""
        if params is None:
            params = {}
        params["X-Plex-Token"] = self._token
        return await super()._request(method, endpoint, params=params, json=json)

    # -- Health check --------------------------------------------------------

    async def test_connection(self) -> bool:
        """GET /identity — lightweight Plex connectivity check."""
        try:
            await self.get("identity")
            return True
        except Exception:
            return False

    # -- Plex-specific endpoints ---------------------------------------------

    async def get_system_status(self) -> Any:
        """GET /identity — server identity information."""
        return await self.get("identity")

    async def get_sessions(self) -> list[Any]:
        """GET /status/sessions — currently playing sessions."""
        r = await self.get("status/sessions")
        return r.get("MediaContainer", {}).get("Metadata", [])

    async def get_transcode_sessions(self) -> list[Any]:
        """GET /transcode/sessions — active transcode sessions."""
        r = await self.get("transcode/sessions")
        return r.get("MediaContainer", {}).get("TranscodeSession", [])
