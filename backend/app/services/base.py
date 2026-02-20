"""Base HTTP client with retry logic for all service clients."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx


class BaseClient:
    """Async HTTP client with exponential-backoff retry on connection errors.

    Subclasses override ``_build_url`` and ``_get_headers`` to customise the
    request for a specific service (API prefix, auth headers, etc.).
    """

    service_name: str = "unknown"

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._client: httpx.AsyncClient | None = None

    # -- URL / header helpers ------------------------------------------------

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for *endpoint*.  Override in subclasses."""
        return f"{self._base_url}/{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        """Return default request headers.  Override in subclasses."""
        return {"Accept": "application/json"}

    # -- Core request machinery ----------------------------------------------

    def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create the underlying ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """Send an HTTP request with iterative retry + exponential backoff.

        Only ``httpx.ConnectError`` triggers a retry; all other exceptions
        propagate immediately.
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()
        client = self._ensure_client()

        last_exc: httpx.ConnectError | None = None
        for attempt in range(self._max_retries):
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    delay = self._retry_base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted — re-raise the last ConnectError.
        raise last_exc  # type: ignore[misc]

    # -- Convenience methods -------------------------------------------------

    async def get(
        self, endpoint: str, *, params: dict[str, Any] | None = None
    ) -> Any:
        """HTTP GET."""
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, *, json: Any | None = None) -> Any:
        """HTTP POST."""
        return await self._request("POST", endpoint, json=json)

    # -- Health check --------------------------------------------------------

    async def test_connection(self) -> bool:
        """GET ``system/status``; return *True* on success, *False* otherwise."""
        try:
            await self.get("system/status")
            return True
        except Exception:
            return False

    # -- Lifecycle -----------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client (if open)."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
