"""Calendar collector — polls Sonarr/Radarr for upcoming episodes and movies."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class CalendarCollector(BaseCollector):
    """Gathers upcoming episodes and movie releases for the next 7 days."""

    async def collect(self) -> None:
        """Poll Sonarr and Radarr calendars and broadcast results."""
        episodes = await self._poll_sonarr_calendar()
        movies = await self._poll_radarr_calendar()

        await self.hub.broadcast("calendar", {
            "episodes": episodes,
            "movies": movies,
        })

    def _date_range(self) -> tuple[str, str]:
        """Return ISO date strings for today and 7 days from now."""
        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        return start, end

    async def _poll_sonarr_calendar(self) -> list[dict[str, Any]]:
        """Fetch upcoming episodes from Sonarr."""
        client = self.clients.get("sonarr")
        if client is None:
            return []
        try:
            start, end = self._date_range()
            entries = await client.get_calendar(start=start, end=end)
            if not isinstance(entries, list):
                return []
            return [
                {
                    "series": ep.get("series", {}).get("title", "")
                    if isinstance(ep.get("series"), dict)
                    else str(ep.get("seriesTitle", "")),
                    "title": ep.get("title", ""),
                    "airDate": ep.get("airDateUtc", ep.get("airDate", "")),
                    "season": ep.get("seasonNumber", 0),
                    "episode": ep.get("episodeNumber", 0),
                    "hasFile": ep.get("hasFile", False),
                }
                for ep in entries
            ]
        except Exception:
            logger.debug("Failed to poll Sonarr calendar")
            return []

    async def _poll_radarr_calendar(self) -> list[dict[str, Any]]:
        """Fetch upcoming movies from Radarr."""
        client = self.clients.get("radarr")
        if client is None:
            return []
        try:
            start, end = self._date_range()
            entries = await client.get_calendar(start=start, end=end)
            if not isinstance(entries, list):
                return []
            return [
                {
                    "title": movie.get("title", ""),
                    "releaseDate": movie.get(
                        "digitalRelease",
                        movie.get("physicalRelease", movie.get("inCinemas", "")),
                    ),
                    "hasFile": movie.get("hasFile", False),
                }
                for movie in entries
            ]
        except Exception:
            logger.debug("Failed to poll Radarr calendar")
            return []
