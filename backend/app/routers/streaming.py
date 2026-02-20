"""Streaming REST endpoint — returns latest streaming snapshot from the hub."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/streaming")
async def get_streaming(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("streaming") or {
        "stream_count": 0,
        "transcode_count": 0,
        "sessions": [],
    }
