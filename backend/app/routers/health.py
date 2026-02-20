"""Health REST endpoint — returns latest health snapshot from the hub."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/health")
async def get_health(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("health") or {"services": []}
