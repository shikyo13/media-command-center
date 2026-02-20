"""Tdarr API client — /api/v2/ prefix, cruddb POST pattern for reads."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseClient


class TdarrClient(BaseClient):
    """HTTP client for the Tdarr v2 API.

    Most collection reads go through the ``POST /api/v2/cruddb`` endpoint
    with a JSON body specifying the collection name and mode.
    """

    service_name = "tdarr"

    def __init__(self, base_url: str, api_key: str = "", **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api/v2/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return headers

    # -- Internal helpers ----------------------------------------------------

    async def _cruddb(self, collection: str, mode: str) -> Any:
        """POST to the ``cruddb`` endpoint for collection reads."""
        return await self.post(
            "cruddb",
            json={"data": {"collection": collection, "mode": mode}},
        )

    # -- Health check --------------------------------------------------------

    async def test_connection(self) -> bool:
        """Verify connectivity by fetching Tdarr status."""
        try:
            await self.get_status()
            return True
        except Exception:
            return False

    # -- Tdarr-specific endpoints --------------------------------------------

    async def get_system_status(self) -> Any:
        """Alias for :meth:`get_status`."""
        return await self.get_status()

    async def get_status(self) -> Any:
        """GET /api/v2/status."""
        return await self.get("status")

    async def get_nodes(self) -> Any:
        """All registered Tdarr nodes."""
        return await self._cruddb("NodeJSONDB", "getAll")

    async def get_statistics(self) -> Any:
        """Library statistics."""
        return await self._cruddb("StatisticsJSONDB", "getAll")

    async def get_staged_files(self) -> Any:
        """Files queued for processing."""
        return await self._cruddb("StagedJSONDB", "getAll")
