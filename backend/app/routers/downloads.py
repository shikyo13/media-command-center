"""Downloads REST endpoint — returns latest downloads snapshot from the hub."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/downloads")
async def get_downloads(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("downloads") or {
        "sabnzbd": {"items": []},
        "sonarr_queue": [],
        "radarr_queue": [],
    }
