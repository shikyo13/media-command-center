"""Abstract base class for all data collectors."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.ws.hub import ConnectionHub

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Periodically collects data from services and broadcasts via the hub.

    Subclasses must implement :meth:`collect` which gathers data from one
    or more service clients and broadcasts results through the hub.
    """

    def __init__(
        self,
        hub: ConnectionHub,
        clients: dict[str, Any],
        interval: float,
    ) -> None:
        self.hub = hub
        self.clients = clients
        self.interval = interval
        self._task: asyncio.Task[None] | None = None

    @abstractmethod
    async def collect(self) -> None:
        """Gather data from services and broadcast via the hub."""

    async def _loop(self) -> None:
        """Run :meth:`collect` in an infinite loop with sleep intervals."""
        while True:
            try:
                await self.collect()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in %s.collect()", type(self).__name__)
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        """Create an asyncio task running the collection loop."""
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Cancel the collection loop task and await its completion."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
