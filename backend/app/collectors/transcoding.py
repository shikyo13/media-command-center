"""Transcoding collector — polls Tdarr for node status and statistics."""

from __future__ import annotations

import logging
from typing import Any

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class TranscodingCollector(BaseCollector):
    """Gathers Tdarr transcoding status, nodes, and queue info."""

    async def collect(self) -> None:
        """Poll Tdarr for nodes, staged files, and statistics."""
        tdarr = self.clients.get("tdarr")
        if tdarr is None:
            await self.hub.broadcast("transcoding", {
                "nodes": [],
                "queue_size": 0,
                "total_files": 0,
                "total_transcodes": 0,
                "size_diff_bytes": 0,
            })
            return

        try:
            nodes_raw = await tdarr.get_nodes()
            staged_raw = await tdarr.get_staged_files()
            stats_raw = await tdarr.get_statistics()

            nodes = self._parse_nodes(nodes_raw)
            queue_size = len(staged_raw) if isinstance(staged_raw, list) else 0
            stats = self._parse_statistics(stats_raw)

            await self.hub.broadcast("transcoding", {
                "nodes": nodes,
                "queue_size": queue_size,
                **stats,
            })
        except Exception:
            logger.debug("Failed to poll Tdarr")
            await self.hub.broadcast("transcoding", {
                "nodes": [],
                "queue_size": 0,
                "total_files": 0,
                "total_transcodes": 0,
                "size_diff_bytes": 0,
            })

    @staticmethod
    def _parse_nodes(nodes_raw: Any) -> list[dict[str, Any]]:
        """Extract node info from Tdarr response."""
        if isinstance(nodes_raw, dict):
            return [
                {
                    "id": node_id,
                    "name": node_data.get("nodeName", node_id),
                    "workers": node_data.get("workers", {}),
                }
                for node_id, node_data in nodes_raw.items()
            ]
        return []

    @staticmethod
    def _parse_statistics(stats_raw: Any) -> dict[str, Any]:
        """Extract summary statistics from Tdarr response."""
        if isinstance(stats_raw, dict):
            return {
                "total_files": stats_raw.get("totalFileCount", 0),
                "total_transcodes": stats_raw.get("totalTranscodeCount", 0),
                "size_diff_bytes": stats_raw.get("sizeDiff", 0),
            }
        return {
            "total_files": 0,
            "total_transcodes": 0,
            "size_diff_bytes": 0,
        }
