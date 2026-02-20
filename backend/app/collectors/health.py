"""Health collector — polls each configured service for online/offline status."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class HealthCollector(BaseCollector):
    """Checks the health of every configured service concurrently.

    Broadcasts a ``health`` message with the status of each service.
    """

    async def collect(self) -> None:
        """Poll all service clients and broadcast results."""
        tasks = [
            self._check_service(name, client)
            for name, client in self.clients.items()
        ]
        results = await asyncio.gather(*tasks)
        await self.hub.broadcast("health", {"services": results})

    async def _check_service(
        self, name: str, client: Any
    ) -> dict[str, Any]:
        """Call ``get_system_status()`` on a single client and time it."""
        start = time.monotonic()
        try:
            response = await client.get_system_status()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            version = self._extract_version(response)
            return {
                "name": name,
                "status": "online",
                "version": version,
                "response_ms": elapsed_ms,
            }
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.debug("Service %s is offline", name)
            return {
                "name": name,
                "status": "offline",
                "version": "",
                "response_ms": elapsed_ms,
            }

    @staticmethod
    def _extract_version(response: Any) -> str:
        """Try common keys to find a version string in the response."""
        if isinstance(response, dict):
            for key in ("version", "Version"):
                if key in response:
                    return str(response[key])
        return ""
