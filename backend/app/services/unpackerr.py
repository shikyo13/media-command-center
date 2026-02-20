"""Unpackerr client — Prometheus text metrics endpoint (not JSON)."""

from __future__ import annotations

import re
from typing import Any

from app.services.base import BaseClient

_METRIC_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{(?P<labels>[^}]*)\})?"
    r"\s+(?P<value>\S+)$"
)


class UnpackerrClient(BaseClient):
    """HTTP client for the Unpackerr Prometheus metrics endpoint.

    Unlike every other service, Unpackerr exposes **plain-text**
    Prometheus metrics rather than JSON.
    """

    service_name = "unpackerr"

    # -- Raw text helper -----------------------------------------------------

    async def _get_text(self, endpoint: str) -> str:
        """GET *endpoint* and return the body as raw text (not JSON)."""
        url = self._build_url(endpoint)
        client = self._ensure_client()
        response = await client.request(
            method="GET",
            url=url,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.text

    # -- Health check --------------------------------------------------------

    async def test_connection(self) -> bool:
        """Verify Unpackerr is reachable by fetching its metrics endpoint."""
        try:
            await self._get_text("metrics")
            return True
        except Exception:
            return False

    # -- Metrics -------------------------------------------------------------

    async def get_system_status(self) -> dict[str, Any]:
        """Return a lightweight summary for the unified status endpoint."""
        metrics = await self.get_metrics()
        return {"service": "Unpackerr", "metrics_count": len(metrics)}

    async def get_metrics(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch and parse the Prometheus metrics into a dict."""
        text = await self._get_text("metrics")
        return self._parse_prometheus(text)

    # -- Prometheus parser ---------------------------------------------------

    @staticmethod
    def _parse_prometheus(text: str) -> dict[str, list[dict[str, Any]]]:
        """Parse Prometheus exposition text into a structured dict.

        Returns a mapping of ``metric_name`` to a list of
        ``{"labels": {...}, "value": float}`` entries.
        """
        result: dict[str, list[dict[str, Any]]] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = _METRIC_RE.match(line)
            if not m:
                continue
            name = m.group("name")
            labels_str = m.group("labels") or ""
            value_str = m.group("value")

            labels: dict[str, str] = {}
            if labels_str:
                for pair in re.findall(r'(\w+)="([^"]*)"', labels_str):
                    labels[pair[0]] = pair[1]

            try:
                value = float(value_str)
            except ValueError:
                continue

            result.setdefault(name, []).append({"labels": labels, "value": value})
        return result
