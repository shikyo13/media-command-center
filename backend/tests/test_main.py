"""Tests for the FastAPI application (main.py)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app


def _test_settings() -> Settings:
    """Create a Settings instance that does not read .env files."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /api/health returns 200 with a 'services' key."""
    application = create_app(settings=_test_settings(), skip_collectors=True)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    assert "services" in r.json()


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """GET /metrics returns 200 with Prometheus text containing mcc_ gauges."""
    application = create_app(settings=_test_settings(), skip_collectors=True)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/metrics")
    assert r.status_code == 200
    assert b"mcc_" in r.content
