"""Transcoding REST endpoint — returns latest transcoding snapshot from the hub."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/transcoding")
async def get_transcoding(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("transcoding") or {"nodes": [], "queue_size": 0}
