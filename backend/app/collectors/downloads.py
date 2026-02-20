"""Downloads collector — polls SABnzbd queue + Sonarr/Radarr import queues."""

from __future__ import annotations

import logging
from typing import Any

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class DownloadsCollector(BaseCollector):
    """Gathers download activity from SABnzbd, Sonarr, and Radarr.

    Gracefully handles missing services by returning empty data.
    """

    async def collect(self) -> None:
        """Poll download queues and broadcast results."""
        sabnzbd_data = await self._poll_sabnzbd()
        sonarr_queue = await self._poll_arr_queue("sonarr")
        radarr_queue = await self._poll_arr_queue("radarr")

        await self.hub.broadcast("downloads", {
            "sabnzbd": sabnzbd_data,
            "sonarr_queue": sonarr_queue,
            "radarr_queue": radarr_queue,
        })

    async def _poll_sabnzbd(self) -> dict[str, Any]:
        """Fetch SABnzbd queue, return structured data."""
        client = self.clients.get("sabnzbd")
        if client is None:
            return {"speed": "", "sizeleft": "", "timeleft": "", "items": []}
        try:
            result = await client.get_queue()
            queue = result.get("queue", {})
            items = [
                {
                    "name": slot.get("filename", ""),
                    "percentage": slot.get("percentage", ""),
                    "sizeleft": slot.get("sizeleft", ""),
                    "status": slot.get("status", ""),
                    "timeleft": slot.get("timeleft", ""),
                }
                for slot in queue.get("slots", [])
            ]
            return {
                "speed": queue.get("speed", ""),
                "sizeleft": queue.get("sizeleft", ""),
                "timeleft": queue.get("timeleft", ""),
                "items": items,
            }
        except Exception:
            logger.debug("Failed to poll SABnzbd queue")
            return {"speed": "", "sizeleft": "", "timeleft": "", "items": []}

    async def _poll_arr_queue(self, name: str) -> list[dict[str, Any]]:
        """Fetch Sonarr or Radarr import queue."""
        client = self.clients.get(name)
        if client is None:
            return []
        try:
            result = await client.get_queue()
            records = result.get("records", [])
            return [
                {
                    "title": rec.get("title", ""),
                    "status": rec.get("status", ""),
                    "sizeleft": rec.get("sizeleft", 0),
                    "size": rec.get("size", 0),
                }
                for rec in records
            ]
        except Exception:
            logger.debug("Failed to poll %s queue", name)
            return []
