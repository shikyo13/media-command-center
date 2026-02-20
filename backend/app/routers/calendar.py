"""Calendar REST endpoint — returns latest calendar snapshot from the hub."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/calendar")
async def get_calendar(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("calendar") or {"episodes": [], "movies": []}
