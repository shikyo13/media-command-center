"""Prometheus metrics — exposes Gauge metrics scraped from hub snapshots."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from prometheus_client import CollectorRegistry, Gauge, generate_latest

# Use a dedicated registry so tests don't clash with the global default.
registry = CollectorRegistry()

# -- Gauges ----------------------------------------------------------------

mcc_service_up = Gauge(
    "mcc_service_up",
    "Whether a service is online (1) or offline (0)",
    ["service"],
    registry=registry,
)

mcc_service_latency = Gauge(
    "mcc_service_latency_seconds",
    "Last measured response latency in seconds",
    ["service"],
    registry=registry,
)

mcc_downloads_active = Gauge(
    "mcc_downloads_active",
    "Number of active downloads",
    registry=registry,
)

mcc_plex_streams_active = Gauge(
    "mcc_plex_streams_active",
    "Number of active Plex streaming sessions",
    registry=registry,
)

mcc_plex_transcode_active = Gauge(
    "mcc_plex_transcode_active",
    "Number of active Plex transcode sessions",
    registry=registry,
)

mcc_tdarr_queue_size = Gauge(
    "mcc_tdarr_queue_size",
    "Number of files pending in the Tdarr queue",
    registry=registry,
)

mcc_tdarr_space_saved_bytes = Gauge(
    "mcc_tdarr_space_saved_bytes",
    "Cumulative space saved by Tdarr transcoding (bytes)",
    registry=registry,
)


# -- Snapshot-to-gauge sync ------------------------------------------------

def update_metrics_from_hub(hub: Any) -> None:
    """Read the latest hub snapshots and update all Prometheus gauges."""

    # Health snapshot
    health = hub.get_snapshot("health")
    if health:
        data = health.get("data", health)
        for svc in data.get("services", []):
            name = svc.get("name", "unknown")
            mcc_service_up.labels(service=name).set(
                1 if svc.get("status") == "online" else 0
            )
            mcc_service_latency.labels(service=name).set(
                svc.get("response_ms", 0) / 1000.0
            )

    # Downloads snapshot
    downloads = hub.get_snapshot("downloads")
    if downloads:
        data = downloads.get("data", downloads)
        count = len(data.get("sabnzbd", {}).get("items", []))
        count += len(data.get("sonarr_queue", []))
        count += len(data.get("radarr_queue", []))
        mcc_downloads_active.set(count)

    # Streaming snapshot
    streaming = hub.get_snapshot("streaming")
    if streaming:
        data = streaming.get("data", streaming)
        mcc_plex_streams_active.set(data.get("stream_count", 0))
        mcc_plex_transcode_active.set(data.get("transcode_count", 0))

    # Transcoding snapshot
    transcoding = hub.get_snapshot("transcoding")
    if transcoding:
        data = transcoding.get("data", transcoding)
        mcc_tdarr_queue_size.set(data.get("queue_size", 0))
        mcc_tdarr_space_saved_bytes.set(data.get("size_diff_bytes", 0))


# -- Router ----------------------------------------------------------------

router = APIRouter()


@router.get("/metrics")
async def get_metrics(request: Request):
    """Prometheus scrape endpoint."""
    from fastapi.responses import Response

    hub = request.app.state.hub
    update_metrics_from_hub(hub)

    return Response(
        content=generate_latest(registry),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
