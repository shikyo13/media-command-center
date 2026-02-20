"""Streaming collector — polls Plex for active sessions."""

from __future__ import annotations

import logging
from typing import Any

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class StreamingCollector(BaseCollector):
    """Gathers active Plex streaming sessions and transcode info."""

    async def collect(self) -> None:
        """Poll Plex sessions and broadcast results."""
        plex = self.clients.get("plex")
        if plex is None:
            await self.hub.broadcast("streaming", {
                "stream_count": 0,
                "transcode_count": 0,
                "sessions": [],
            })
            return

        try:
            sessions = await plex.get_sessions()
            parsed = [self._parse_session(s) for s in sessions]
            transcode_count = sum(
                1 for s in parsed if s["decision"] == "transcode"
            )
            await self.hub.broadcast("streaming", {
                "stream_count": len(parsed),
                "transcode_count": transcode_count,
                "sessions": parsed,
            })
        except Exception:
            logger.debug("Failed to poll Plex sessions")
            await self.hub.broadcast("streaming", {
                "stream_count": 0,
                "transcode_count": 0,
                "sessions": [],
            })

    @staticmethod
    def _parse_session(session: dict[str, Any]) -> dict[str, Any]:
        """Extract relevant fields from a Plex session object."""
        # Determine playback decision from Media -> Part -> Stream or top-level
        decision = "directplay"
        media_list = session.get("Media", [])
        if media_list:
            parts = media_list[0].get("Part", [])
            if parts:
                decision = parts[0].get("decision", "directplay")
        # Also check TranscodeSession for an explicit decision
        transcode = session.get("TranscodeSession", {})
        if transcode:
            decision = "transcode"

        return {
            "user": session.get("User", {}).get("title", ""),
            "title": session.get("title", ""),
            "grandparentTitle": session.get("grandparentTitle", ""),
            "parentIndex": session.get("parentIndex"),
            "index": session.get("index"),
            "decision": decision,
        }
