"""FastAPI application factory and entry point."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.ws.hub import ConnectionHub

from app.collectors.health import HealthCollector
from app.collectors.downloads import DownloadsCollector
from app.collectors.streaming import StreamingCollector
from app.collectors.transcoding import TranscodingCollector
from app.collectors.calendar import CalendarCollector

from app.routers import health, downloads, streaming, transcoding, calendar
from app.metrics import router as metrics_router

from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.prowlarr import ProwlarrClient
from app.services.bazarr import BazarrClient
from app.services.overseerr import OverseerrClient
from app.services.plex import PlexClient
from app.services.tdarr import TdarrClient
from app.services.sabnzbd import SABnzbdClient
from app.services.unpackerr import UnpackerrClient

logger = logging.getLogger(__name__)

# -- Client factory registry ------------------------------------------------

CLIENT_FACTORIES: dict[str, Any] = {
    "sonarr": lambda s: SonarrClient(s.sonarr_url, s.sonarr_api_key),
    "radarr": lambda s: RadarrClient(s.radarr_url, s.radarr_api_key),
    "prowlarr": lambda s: ProwlarrClient(s.prowlarr_url, s.prowlarr_api_key),
    "bazarr": lambda s: BazarrClient(s.bazarr_url, s.bazarr_api_key),
    "overseerr": lambda s: OverseerrClient(s.overseerr_url, s.overseerr_api_key),
    "plex": lambda s: PlexClient(s.plex_url, s.plex_token),
    "tdarr": lambda s: TdarrClient(s.tdarr_url, s.tdarr_api_key),
    "sabnzbd": lambda s: SABnzbdClient(s.sabnzbd_url, s.sabnzbd_api_key),
    "unpackerr": lambda s: UnpackerrClient(s.unpackerr_url),
}

# -- Collector intervals (seconds) -----------------------------------------

COLLECTOR_INTERVALS: dict[str, float] = {
    "health": 30,
    "downloads": 5,
    "streaming": 5,
    "transcoding": 10,
    "calendar": 300,
}


def _build_clients(settings: Settings) -> dict[str, Any]:
    """Instantiate service clients for every configured service."""
    clients: dict[str, Any] = {}
    for name in settings.configured_services():
        factory = CLIENT_FACTORIES.get(name)
        if factory is not None:
            clients[name] = factory(settings)
    return clients


def create_app(
    settings: Settings | None = None,
    skip_collectors: bool = False,
) -> FastAPI:
    """Build and return a fully-configured FastAPI application.

    Parameters
    ----------
    settings:
        Pre-built settings instance.  If *None*, a new ``Settings()``
        is created (which reads from environment / ``.env``).
    skip_collectors:
        When *True*, collectors are not started (useful for testing).
    """
    if settings is None:
        settings = Settings()

    hub = ConnectionHub()
    clients = _build_clients(settings)
    collectors: list[Any] = []

    if not skip_collectors:
        collectors = [
            HealthCollector(hub, clients, COLLECTOR_INTERVALS["health"]),
            DownloadsCollector(hub, clients, COLLECTOR_INTERVALS["downloads"]),
            StreamingCollector(hub, clients, COLLECTOR_INTERVALS["streaming"]),
            TranscodingCollector(hub, clients, COLLECTOR_INTERVALS["transcoding"]),
            CalendarCollector(hub, clients, COLLECTOR_INTERVALS["calendar"]),
        ]

    @asynccontextmanager
    async def lifespan(application: FastAPI):  # noqa: ARG001
        # Start collectors
        for collector in collectors:
            collector.start()
        logger.info(
            "Started %d collectors for %d services",
            len(collectors),
            len(clients),
        )
        yield
        # Stop collectors
        for collector in collectors:
            await collector.stop()
        # Close all HTTP clients
        for client in clients.values():
            await client.close()
        logger.info("Shutdown complete")

    application = FastAPI(
        title="Media Command Center",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store hub on app state so routers can access it.
    application.state.hub = hub

    # CORS middleware — allow all origins for the dashboard SPA.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    application.include_router(health.router)
    application.include_router(downloads.router)
    application.include_router(streaming.router)
    application.include_router(transcoding.router)
    application.include_router(calendar.router)

    # Prometheus metrics
    application.include_router(metrics_router)

    # WebSocket endpoint
    @application.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        hub.connect(ws)
        try:
            # Send current snapshots on connect
            for msg_type in ("health", "downloads", "streaming", "transcoding", "calendar"):
                snapshot = hub.get_snapshot(msg_type)
                if snapshot:
                    await ws.send_text(json.dumps(snapshot))
            # Keep alive — wait for client messages (or disconnect)
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(ws)

    return application


# Module-level instance for ``uvicorn app.main:app``
app = create_app()
