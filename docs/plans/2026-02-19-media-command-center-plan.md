# Media Command Center — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone, open-source web dashboard for monitoring a media server stack (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, Plex, Tdarr, SABnzbd, Unpackerr, Recyclarr) with real-time WebSocket updates, glassmorphism cyberpunk UI, and Prometheus metrics export.

**Architecture:** Python FastAPI backend with its own httpx service clients, asyncio background collectors that push state through a WebSocket hub. React + Vite + Tailwind + shadcn/ui frontend with Zustand stores consuming WS messages. Docker Compose deployment.

**Tech Stack:** Python 3.12, FastAPI, httpx, Pydantic, uvicorn | React 18, Vite, TypeScript, Tailwind CSS 4, shadcn/ui, Zustand, Recharts | Docker

**Design Doc:** `docs/plans/2026-02-19-media-command-center-design.md`

---

## Phase 1: Backend Project Scaffolding

### Task 1: Initialize backend project structure

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/collectors/__init__.py`
- Create: `backend/app/ws/__init__.py`
- Create: `backend/app/routers/__init__.py`

**Step 1: Create directory structure**

```bash
cd C:\Users\Shikyo\media-command-center
mkdir -p backend/app/services backend/app/collectors backend/app/ws backend/app/routers
touch backend/app/__init__.py backend/app/services/__init__.py
touch backend/app/collectors/__init__.py backend/app/ws/__init__.py backend/app/routers/__init__.py
```

**Step 2: Create pyproject.toml**

Create `backend/pyproject.toml`:

```toml
[project]
name = "media-command-center"
version = "0.1.0"
description = "Unified monitoring dashboard for media server stacks"
requires-python = ">=3.11"
license = "MIT"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "httpx>=0.28.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "prometheus-client>=0.22.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.25.0",
    "respx>=0.22.0",
    "httpx",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create .env.example**

Create `backend/.env.example`:

```env
# Media Command Center Configuration
# Only configured services will appear on the dashboard.

# --- Sonarr ---
SONARR_URL=http://localhost:8989
SONARR_API_KEY=

# --- Radarr ---
RADARR_URL=http://localhost:7878
RADARR_API_KEY=

# --- Prowlarr ---
PROWLARR_URL=http://localhost:9696
PROWLARR_API_KEY=

# --- Bazarr ---
BAZARR_URL=http://localhost:6767
BAZARR_API_KEY=

# --- Overseerr ---
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=

# --- Plex ---
PLEX_URL=http://localhost:32400
PLEX_TOKEN=

# --- Tdarr ---
TDARR_URL=http://localhost:8265
TDARR_API_KEY=

# --- SABnzbd ---
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=

# --- Unpackerr ---
UNPACKERR_URL=http://localhost:5656

# --- Recyclarr ---
RECYCLARR_EXE_PATH=

# --- Dashboard ---
MCC_HOST=0.0.0.0
MCC_PORT=8880
```

**Step 4: Install dev dependencies**

```bash
cd C:\Users\Shikyo\media-command-center\backend
pip install -e ".[dev]"
```

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend project structure"
```

---

### Task 2: Configuration module

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

**Step 1: Write the failing test**

Create `backend/tests/__init__.py` (empty) and `backend/tests/test_config.py`:

```python
"""Tests for configuration loading."""

import os
import pytest
from app.config import Settings


class TestSettings:

    def test_defaults(self):
        """Settings loads with no env vars — no services configured."""
        settings = Settings(_env_file=None)
        assert settings.mcc_host == "0.0.0.0"
        assert settings.mcc_port == 8880
        assert settings.configured_services() == []

    def test_sonarr_configured(self, monkeypatch):
        monkeypatch.setenv("SONARR_URL", "http://localhost:8989")
        monkeypatch.setenv("SONARR_API_KEY", "test-key")
        settings = Settings(_env_file=None)
        services = settings.configured_services()
        assert "sonarr" in services

    def test_plex_configured(self, monkeypatch):
        monkeypatch.setenv("PLEX_URL", "http://localhost:32400")
        monkeypatch.setenv("PLEX_TOKEN", "test-token")
        settings = Settings(_env_file=None)
        assert "plex" in settings.configured_services()

    def test_tdarr_configured_no_api_key(self, monkeypatch):
        """Tdarr and Unpackerr don't need API keys."""
        monkeypatch.setenv("TDARR_URL", "http://localhost:8265")
        settings = Settings(_env_file=None)
        assert "tdarr" in settings.configured_services()

    def test_unpackerr_configured(self, monkeypatch):
        monkeypatch.setenv("UNPACKERR_URL", "http://localhost:5656")
        settings = Settings(_env_file=None)
        assert "unpackerr" in settings.configured_services()
```

**Step 2: Run test to verify it fails**

```bash
cd C:\Users\Shikyo\media-command-center\backend
python -m pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.config'`

**Step 3: Write implementation**

Create `backend/app/config.py`:

```python
"""Application configuration — loads service URLs/keys from environment."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All settings loaded from env vars or .env file."""

    model_config = {"env_file": ".env", "extra": "ignore"}

    # Dashboard
    mcc_host: str = Field(default="0.0.0.0")
    mcc_port: int = Field(default=8880)

    # Sonarr
    sonarr_url: str = ""
    sonarr_api_key: str = ""

    # Radarr
    radarr_url: str = ""
    radarr_api_key: str = ""

    # Prowlarr
    prowlarr_url: str = ""
    prowlarr_api_key: str = ""

    # Bazarr
    bazarr_url: str = ""
    bazarr_api_key: str = ""

    # Overseerr
    overseerr_url: str = ""
    overseerr_api_key: str = ""

    # Plex
    plex_url: str = ""
    plex_token: str = ""

    # Tdarr
    tdarr_url: str = ""
    tdarr_api_key: str = ""

    # SABnzbd
    sabnzbd_url: str = ""
    sabnzbd_api_key: str = ""

    # Unpackerr
    unpackerr_url: str = ""

    # Recyclarr
    recyclarr_exe_path: str = ""

    def configured_services(self) -> list[str]:
        """Return list of service names that have sufficient config."""
        services = []
        # URL + API key services
        for name in ("sonarr", "radarr", "prowlarr", "bazarr", "overseerr", "sabnzbd"):
            if getattr(self, f"{name}_url") and getattr(self, f"{name}_api_key"):
                services.append(name)
        # Plex: URL + token
        if self.plex_url and self.plex_token:
            services.append("plex")
        # URL-only services (no API key required)
        for name in ("tdarr", "unpackerr"):
            if getattr(self, f"{name}_url"):
                services.append(name)
        # Recyclarr: exe path
        if self.recyclarr_exe_path:
            services.append("recyclarr")
        return services
```

**Step 4: Run test to verify it passes**

```bash
cd C:\Users\Shikyo\media-command-center\backend
python -m pytest tests/test_config.py -v
```

Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/
git commit -m "feat: add configuration module with service detection"
```

---

### Task 3: Base HTTP client

**Files:**
- Create: `backend/app/services/base.py`
- Test: `backend/tests/services/__init__.py`
- Test: `backend/tests/services/test_base.py`

**Step 1: Write the failing test**

Create `backend/tests/services/__init__.py` (empty) and `backend/tests/services/test_base.py`:

```python
"""Tests for base HTTP client."""

import pytest
import httpx
import respx
from app.services.base import BaseClient


class ConcreteClient(BaseClient):
    """Minimal concrete subclass for testing."""

    service_name = "test"

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}


class TestBaseClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_success(self):
        route = respx.get("http://test:9999/api/status").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        async with ConcreteClient("http://test:9999") as client:
            result = await client.get("status")
        assert result == {"ok": True}
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_on_connect_error(self):
        route = respx.get("http://test:9999/api/status").mock(
            side_effect=[httpx.ConnectError("refused"), httpx.Response(200, json={"ok": True})]
        )
        async with ConcreteClient("http://test:9999", max_retries=2, retry_base_delay=0.01) as client:
            result = await client.get("status")
        assert result == {"ok": True}
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        respx.get("http://test:9999/api/status").mock(
            side_effect=httpx.ConnectError("refused")
        )
        async with ConcreteClient("http://test:9999", max_retries=1, retry_base_delay=0.01) as client:
            with pytest.raises(httpx.ConnectError):
                await client.get("status")

    @respx.mock
    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        respx.get("http://test:9999/api/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )
        async with ConcreteClient("http://test:9999") as client:
            assert await client.test_connection() is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        respx.get("http://test:9999/api/system/status").mock(
            side_effect=httpx.ConnectError("refused")
        )
        async with ConcreteClient("http://test:9999", max_retries=0) as client:
            assert await client.test_connection() is False
```

**Step 2: Run test to verify it fails**

```bash
cd C:\Users\Shikyo\media-command-center\backend
python -m pytest tests/services/test_base.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.base'`

**Step 3: Write implementation**

Create `backend/app/services/base.py`:

```python
"""Base HTTP client with retry logic."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BaseClient:
    """Base async HTTP client with exponential-backoff retries."""

    service_name: str = "unknown"

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        last_error: Exception | None = None
        url = self._build_url(endpoint)

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=json,
                )
                response.raise_for_status()
                if not response.content:
                    return None
                return response.json()
            except httpx.ConnectError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_base_delay * (2 ** attempt)
                    logger.warning(
                        "%s: connect failed, retry %d/%d in %.1fs",
                        self.service_name, attempt + 1, self.max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
            except httpx.TimeoutException:
                raise
            except httpx.HTTPStatusError:
                raise

        raise last_error  # type: ignore[misc]

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", endpoint, json=json)

    async def test_connection(self) -> bool:
        try:
            await self.get("system/status")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/services/test_base.py -v
```

Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/services/base.py backend/tests/services/
git commit -m "feat: add base HTTP client with retry logic"
```

---

### Task 4: Service clients — Arr services (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr)

These all follow the same pattern: `X-Api-Key` header, `/api/v3/` URL prefix. We only need the endpoints relevant to the dashboard collectors.

**Files:**
- Create: `backend/app/services/sonarr.py`
- Create: `backend/app/services/radarr.py`
- Create: `backend/app/services/prowlarr.py`
- Create: `backend/app/services/bazarr.py`
- Create: `backend/app/services/overseerr.py`
- Test: `backend/tests/services/test_arr_clients.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_arr_clients.py`:

```python
"""Tests for Arr service clients (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr)."""

import pytest
import httpx
import respx

from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.prowlarr import ProwlarrClient
from app.services.bazarr import BazarrClient
from app.services.overseerr import OverseerrClient


class TestSonarrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_queue(self):
        respx.get("http://sonarr:8989/api/v3/queue").mock(
            return_value=httpx.Response(200, json={"records": []})
        )
        async with SonarrClient("http://sonarr:8989", "key") as c:
            result = await c.get_queue()
        assert result == {"records": []}

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_calendar(self):
        respx.get("http://sonarr:8989/api/v3/calendar").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with SonarrClient("http://sonarr:8989", "key") as c:
            result = await c.get_calendar()
        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_headers_include_api_key(self):
        route = respx.get("http://sonarr:8989/api/v3/system/status").mock(
            return_value=httpx.Response(200, json={"version": "4"})
        )
        async with SonarrClient("http://sonarr:8989", "my-key") as c:
            await c.get_system_status()
        assert route.calls[0].request.headers["X-Api-Key"] == "my-key"


class TestRadarrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_queue(self):
        respx.get("http://radarr:7878/api/v3/queue").mock(
            return_value=httpx.Response(200, json={"records": []})
        )
        async with RadarrClient("http://radarr:7878", "key") as c:
            result = await c.get_queue()
        assert result == {"records": []}

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_calendar(self):
        respx.get("http://radarr:7878/api/v3/calendar").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with RadarrClient("http://radarr:7878", "key") as c:
            result = await c.get_calendar()
        assert result == []


class TestProwlarrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_system_status(self):
        respx.get("http://prowlarr:9696/api/v1/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )
        async with ProwlarrClient("http://prowlarr:9696", "key") as c:
            result = await c.get_system_status()
        assert result["version"] == "1.0"


class TestBazarrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_system_status(self):
        respx.get("http://bazarr:6767/api/system/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )
        async with BazarrClient("http://bazarr:6767", "key") as c:
            result = await c.get_system_status()
        assert result["version"] == "1.0"


class TestOverseerrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_system_status(self):
        respx.get("http://overseerr:5055/api/v1/status").mock(
            return_value=httpx.Response(200, json={"version": "1.0"})
        )
        async with OverseerrClient("http://overseerr:5055", "key") as c:
            result = await c.get_system_status()
        assert result["version"] == "1.0"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/services/test_arr_clients.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementations**

Create `backend/app/services/sonarr.py`:

```python
"""Sonarr client — calendar + queue for dashboard collectors."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class SonarrClient(BaseClient):
    service_name = "Sonarr"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/v3/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key, "Accept": "application/json"}

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("system/status")

    async def get_queue(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        return await self.get("queue", params={"page": page, "pageSize": page_size})

    async def get_calendar(self, start: str | None = None, end: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self.get("calendar", params=params or None)
```

Create `backend/app/services/radarr.py`:

```python
"""Radarr client — calendar + queue for dashboard collectors."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class RadarrClient(BaseClient):
    service_name = "Radarr"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/v3/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key, "Accept": "application/json"}

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("system/status")

    async def get_queue(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        return await self.get("queue", params={"page": page, "pageSize": page_size})

    async def get_calendar(self, start: str | None = None, end: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self.get("calendar", params=params or None)
```

Create `backend/app/services/prowlarr.py`:

```python
"""Prowlarr client — health check only for dashboard."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class ProwlarrClient(BaseClient):
    service_name = "Prowlarr"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key, "Accept": "application/json"}

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("system/status")
```

Create `backend/app/services/bazarr.py`:

```python
"""Bazarr client — health check only for dashboard."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class BazarrClient(BaseClient):
    service_name = "Bazarr"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"apikey": self._api_key, "Accept": "application/json"}

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("system/status")
```

Create `backend/app/services/overseerr.py`:

```python
"""Overseerr client — health check only for dashboard."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class OverseerrClient(BaseClient):
    service_name = "Overseerr"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key, "Accept": "application/json"}

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("status")
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/services/test_arr_clients.py -v
```

Expected: All 8 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/services/
git commit -m "feat: add Sonarr, Radarr, Prowlarr, Bazarr, Overseerr clients"
```

---

### Task 5: Service clients — Plex, SABnzbd, Tdarr, Unpackerr

**Files:**
- Create: `backend/app/services/plex.py`
- Create: `backend/app/services/sabnzbd.py`
- Create: `backend/app/services/tdarr.py`
- Create: `backend/app/services/unpackerr.py`
- Test: `backend/tests/services/test_custom_clients.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_custom_clients.py`:

```python
"""Tests for non-standard service clients (Plex, SABnzbd, Tdarr, Unpackerr)."""

import pytest
import httpx
import respx

from app.services.plex import PlexClient
from app.services.sabnzbd import SABnzbdClient
from app.services.tdarr import TdarrClient
from app.services.unpackerr import UnpackerrClient


class TestPlexClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_sessions(self):
        respx.get("http://plex:32400/status/sessions").mock(
            return_value=httpx.Response(200, json={
                "MediaContainer": {"Metadata": [{"title": "Movie"}]}
            })
        )
        async with PlexClient("http://plex:32400", "tok") as c:
            result = await c.get_sessions()
        assert result == [{"title": "Movie"}]

    @respx.mock
    @pytest.mark.asyncio
    async def test_token_in_headers_and_params(self):
        route = respx.get("http://plex:32400/identity").mock(
            return_value=httpx.Response(200, json={"MediaContainer": {}})
        )
        async with PlexClient("http://plex:32400", "my-tok") as c:
            await c.test_connection()
        req = route.calls[0].request
        assert req.headers["X-Plex-Token"] == "my-tok"
        assert "X-Plex-Token=my-tok" in str(req.url)


class TestSABnzbdClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_queue(self):
        respx.get("http://sab:8080/api").mock(
            return_value=httpx.Response(200, json={"queue": {"slots": []}})
        )
        async with SABnzbdClient("http://sab:8080", "key") as c:
            result = await c.get_queue()
        assert "queue" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_api_key_in_params(self):
        route = respx.get("http://sab:8080/api").mock(
            return_value=httpx.Response(200, json={"version": "4.0"})
        )
        async with SABnzbdClient("http://sab:8080", "my-key") as c:
            await c.get_version()
        assert "apikey=my-key" in str(route.calls[0].request.url)


class TestTdarrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_status(self):
        respx.get("http://tdarr:8265/api/v2/status").mock(
            return_value=httpx.Response(200, json={"nodes": {}})
        )
        async with TdarrClient("http://tdarr:8265") as c:
            result = await c.get_status()
        assert "nodes" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_staged_files(self):
        respx.post("http://tdarr:8265/api/v2/cruddb").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with TdarrClient("http://tdarr:8265") as c:
            result = await c.get_staged_files()
        assert result == []


class TestUnpackerrClient:

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        metrics_text = (
            '# HELP unpackerr_extractions_total Total extractions.\n'
            '# TYPE unpackerr_extractions_total counter\n'
            'unpackerr_extractions_total{app="sonarr"} 42\n'
            'unpackerr_extractions_total{app="radarr"} 18\n'
        )
        respx.get("http://unp:5656/metrics").mock(
            return_value=httpx.Response(200, text=metrics_text)
        )
        async with UnpackerrClient("http://unp:5656") as c:
            result = await c.get_metrics()
        assert "unpackerr_extractions_total" in result
        assert len(result["unpackerr_extractions_total"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_test_connection(self):
        respx.get("http://unp:5656/metrics").mock(
            return_value=httpx.Response(200, text="# ok")
        )
        async with UnpackerrClient("http://unp:5656") as c:
            assert await c.test_connection() is True
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/services/test_custom_clients.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementations**

Create `backend/app/services/plex.py`:

```python
"""Plex Media Server client — dual-auth (header + query param)."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class PlexClient(BaseClient):
    service_name = "Plex"

    def __init__(self, base_url: str, token: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._token = token

    def _get_headers(self) -> dict[str, str]:
        return {"X-Plex-Token": self._token, "Accept": "application/json"}

    async def _request(self, method, endpoint, params=None, json=None) -> Any:
        if params is None:
            params = {}
        params["X-Plex-Token"] = self._token
        return await super()._request(method, endpoint, params, json)

    async def test_connection(self) -> bool:
        try:
            await self.get("identity")
            return True
        except Exception:
            return False

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get("identity")

    async def get_sessions(self) -> list[dict[str, Any]]:
        r = await self.get("status/sessions")
        return r.get("MediaContainer", {}).get("Metadata", [])

    async def get_transcode_sessions(self) -> list[dict[str, Any]]:
        r = await self.get("transcode/sessions")
        return r.get("MediaContainer", {}).get("TranscodeSession", [])
```

Create `backend/app/services/sabnzbd.py`:

```python
"""SABnzbd client — single endpoint, query-param auth."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class SABnzbdClient(BaseClient):
    service_name = "SABnzbd"

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api"

    async def _api(self, mode: str, **params: Any) -> Any:
        query = {"mode": mode, "apikey": self._api_key, "output": "json", **params}
        return await self.get("", params=query)

    async def test_connection(self) -> bool:
        try:
            await self._api("version")
            return True
        except Exception:
            return False

    async def get_system_status(self) -> dict[str, Any]:
        return await self._api("fullstatus")

    async def get_queue(self) -> dict[str, Any]:
        return await self._api("queue")

    async def get_version(self) -> dict[str, Any]:
        return await self._api("version")
```

Create `backend/app/services/tdarr.py`:

```python
"""Tdarr client — /api/v2/ with optional x-api-key."""

from __future__ import annotations
from typing import Any
from .base import BaseClient


class TdarrClient(BaseClient):
    service_name = "Tdarr"

    def __init__(self, base_url: str, api_key: str = "", **kwargs):
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/v2/{endpoint.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return headers

    async def _cruddb(self, collection: str, mode: str) -> Any:
        return await self.post("cruddb", json={"data": {"collection": collection, "mode": mode}})

    async def test_connection(self) -> bool:
        try:
            await self.get_status()
            return True
        except Exception:
            return False

    async def get_system_status(self) -> dict[str, Any]:
        return await self.get_status()

    async def get_status(self) -> dict[str, Any]:
        return await self.get("status")

    async def get_nodes(self) -> Any:
        return await self._cruddb("NodeJSONDB", "getAll")

    async def get_statistics(self) -> Any:
        return await self._cruddb("StatisticsJSONDB", "getAll")

    async def get_staged_files(self) -> Any:
        return await self._cruddb("StagedJSONDB", "getAll")
```

Create `backend/app/services/unpackerr.py`:

```python
"""Unpackerr client — Prometheus metrics endpoint."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseClient

_METRIC_RE = re.compile(
    r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>\S+)$'
)


class UnpackerrClient(BaseClient):
    service_name = "Unpackerr"

    async def _get_text(self, endpoint: str) -> str:
        url = self._build_url(endpoint)
        response = await self.client.request(
            method="GET", url=url, headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.text

    async def test_connection(self) -> bool:
        try:
            await self._get_text("metrics")
            return True
        except Exception:
            return False

    async def get_system_status(self) -> dict[str, Any]:
        metrics = await self.get_metrics()
        return {"service": "Unpackerr", "metrics_count": len(metrics)}

    async def get_metrics(self) -> dict[str, list[dict[str, Any]]]:
        text = await self._get_text("metrics")
        return self._parse_prometheus(text)

    @staticmethod
    def _parse_prometheus(text: str) -> dict[str, list[dict[str, Any]]]:
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
            labels = {}
            if labels_str:
                for pair in re.findall(r'(\w+)="([^"]*)"', labels_str):
                    labels[pair[0]] = pair[1]
            try:
                value = float(value_str)
            except ValueError:
                continue
            result.setdefault(name, []).append({"labels": labels, "value": value})
        return result
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/services/test_custom_clients.py -v
```

Expected: All 8 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/services/
git commit -m "feat: add Plex, SABnzbd, Tdarr, Unpackerr clients"
```

---

### Task 6: WebSocket connection hub

**Files:**
- Create: `backend/app/ws/hub.py`
- Test: `backend/tests/test_ws_hub.py`

**Step 1: Write the failing test**

Create `backend/tests/test_ws_hub.py`:

```python
"""Tests for WebSocket hub."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ws.hub import ConnectionHub


class TestConnectionHub:

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        hub = ConnectionHub()
        ws = MagicMock()
        hub.connect(ws)
        assert len(hub.connections) == 1
        hub.disconnect(ws)
        assert len(hub.connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        hub = ConnectionHub()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        hub.connect(ws1)
        hub.connect(ws2)
        await hub.broadcast("health", {"status": "ok"})
        # Both get the message
        assert ws1.send_text.call_count == 1
        assert ws2.send_text.call_count == 1
        msg = json.loads(ws1.send_text.call_args[0][0])
        assert msg["type"] == "health"
        assert msg["data"] == {"status": "ok"}
        assert "timestamp" in msg

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        hub = ConnectionHub()
        ws_good = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_text.side_effect = Exception("closed")
        hub.connect(ws_good)
        hub.connect(ws_dead)
        await hub.broadcast("health", {})
        # Dead connection removed
        assert len(hub.connections) == 1
        assert ws_good in hub.connections

    @pytest.mark.asyncio
    async def test_get_snapshot(self):
        hub = ConnectionHub()
        await hub.broadcast("health", {"ok": True})
        snapshot = hub.get_snapshot("health")
        assert snapshot == {"ok": True}

    @pytest.mark.asyncio
    async def test_get_snapshot_missing(self):
        hub = ConnectionHub()
        assert hub.get_snapshot("nonexistent") is None
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_ws_hub.py -v
```

Expected: FAIL

**Step 3: Write implementation**

Create `backend/app/ws/hub.py`:

```python
"""WebSocket connection manager and broadcast hub."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionHub:
    """Manages WebSocket connections and broadcasts collector updates."""

    def __init__(self):
        self.connections: list[WebSocket] = []
        self._snapshots: dict[str, Any] = {}

    def connect(self, ws: WebSocket) -> None:
        self.connections.append(ws)
        logger.info("WS connected — %d active", len(self.connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.connections:
            self.connections.remove(ws)
        logger.info("WS disconnected — %d active", len(self.connections))

    async def broadcast(self, msg_type: str, data: Any) -> None:
        """Broadcast a message to all connected clients."""
        self._snapshots[msg_type] = data
        if not self.connections:
            return

        message = json.dumps({
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        })

        dead: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    def get_snapshot(self, msg_type: str) -> Any | None:
        """Return the last broadcast data for a given type (for REST fallback)."""
        return self._snapshots.get(msg_type)
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_ws_hub.py -v
```

Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/ws/ backend/tests/test_ws_hub.py
git commit -m "feat: add WebSocket connection hub with snapshot cache"
```

---

### Task 7: Base collector + Health collector

**Files:**
- Create: `backend/app/collectors/base.py`
- Create: `backend/app/collectors/health.py`
- Test: `backend/tests/collectors/__init__.py`
- Test: `backend/tests/collectors/test_health.py`

**Step 1: Write the failing test**

Create `backend/tests/collectors/__init__.py` (empty) and `backend/tests/collectors/test_health.py`:

```python
"""Tests for health collector."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.collectors.health import HealthCollector
from app.ws.hub import ConnectionHub


class TestHealthCollector:

    @pytest.mark.asyncio
    async def test_collect_all_healthy(self):
        hub = ConnectionHub()
        clients = {
            "sonarr": AsyncMock(service_name="Sonarr"),
            "plex": AsyncMock(service_name="Plex"),
        }
        clients["sonarr"].test_connection.return_value = True
        clients["sonarr"].get_system_status.return_value = {"version": "4.0"}
        clients["plex"].test_connection.return_value = True
        clients["plex"].get_system_status.return_value = {"version": "1.40"}

        collector = HealthCollector(hub, clients, interval=30)
        await collector.collect()

        snapshot = hub.get_snapshot("health")
        assert len(snapshot["services"]) == 2
        sonarr = next(s for s in snapshot["services"] if s["name"] == "sonarr")
        assert sonarr["status"] == "online"

    @pytest.mark.asyncio
    async def test_collect_service_offline(self):
        hub = ConnectionHub()
        clients = {
            "sonarr": AsyncMock(service_name="Sonarr"),
        }
        clients["sonarr"].test_connection.return_value = False
        clients["sonarr"].get_system_status.side_effect = Exception("down")

        collector = HealthCollector(hub, clients, interval=30)
        await collector.collect()

        snapshot = hub.get_snapshot("health")
        sonarr = snapshot["services"][0]
        assert sonarr["status"] == "offline"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/collectors/test_health.py -v
```

Expected: FAIL

**Step 3: Write implementations**

Create `backend/app/collectors/base.py`:

```python
"""Base collector — asyncio background loop with error handling."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from ..ws.hub import ConnectionHub

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Background poller that periodically collects data and pushes to WS hub."""

    def __init__(self, hub: ConnectionHub, clients: dict, interval: float):
        self.hub = hub
        self.clients = clients
        self.interval = interval
        self._task: asyncio.Task | None = None

    @abstractmethod
    async def collect(self) -> None:
        """Perform one collection cycle."""

    async def _loop(self) -> None:
        while True:
            try:
                await self.collect()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("%s: collection failed", self.__class__.__name__)
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())
        logger.info("%s: started (interval=%ss)", self.__class__.__name__, self.interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
```

Create `backend/app/collectors/health.py`:

```python
"""Health collector — checks all configured services."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import BaseCollector


class HealthCollector(BaseCollector):
    """Polls each service for health status every interval."""

    async def collect(self) -> None:
        services: list[dict[str, Any]] = []

        async def check(name: str, client: Any) -> dict[str, Any]:
            start = time.monotonic()
            try:
                status_data = await client.get_system_status()
                elapsed_ms = round((time.monotonic() - start) * 1000)
                version = ""
                if isinstance(status_data, dict):
                    version = status_data.get("version", "")
                return {
                    "name": name,
                    "status": "online",
                    "version": str(version),
                    "response_ms": elapsed_ms,
                }
            except Exception:
                elapsed_ms = round((time.monotonic() - start) * 1000)
                return {
                    "name": name,
                    "status": "offline",
                    "version": "",
                    "response_ms": elapsed_ms,
                }

        tasks = [check(name, client) for name, client in self.clients.items()]
        services = await asyncio.gather(*tasks)

        await self.hub.broadcast("health", {"services": list(services)})
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/collectors/test_health.py -v
```

Expected: All 2 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/collectors/ backend/tests/collectors/
git commit -m "feat: add base collector and health collector"
```

---

### Task 8: Downloads collector

**Files:**
- Create: `backend/app/collectors/downloads.py`
- Test: `backend/tests/collectors/test_downloads.py`

**Step 1: Write the failing test**

Create `backend/tests/collectors/test_downloads.py`:

```python
"""Tests for downloads collector."""

import pytest
from unittest.mock import AsyncMock
from app.collectors.downloads import DownloadsCollector
from app.ws.hub import ConnectionHub


class TestDownloadsCollector:

    @pytest.mark.asyncio
    async def test_collect_sabnzbd_queue(self):
        hub = ConnectionHub()
        sab = AsyncMock()
        sab.get_queue.return_value = {
            "queue": {
                "speed": "10.5 M",
                "sizeleft": "1.2 GB",
                "timeleft": "00:05:30",
                "slots": [
                    {"filename": "Show.S01E01", "percentage": "45", "sizeleft": "500 MB",
                     "status": "Downloading", "timeleft": "00:02:00"},
                ],
            }
        }
        sonarr = AsyncMock()
        sonarr.get_queue.return_value = {"records": []}
        radarr = AsyncMock()
        radarr.get_queue.return_value = {"records": []}

        collector = DownloadsCollector(hub, {"sabnzbd": sab, "sonarr": sonarr, "radarr": radarr}, interval=10)
        await collector.collect()

        snapshot = hub.get_snapshot("downloads")
        assert snapshot["sabnzbd"]["speed"] == "10.5 M"
        assert len(snapshot["sabnzbd"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_collect_missing_services(self):
        """Gracefully handles missing services."""
        hub = ConnectionHub()
        collector = DownloadsCollector(hub, {}, interval=10)
        await collector.collect()
        snapshot = hub.get_snapshot("downloads")
        assert snapshot["sabnzbd"]["items"] == []
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/collectors/test_downloads.py -v
```

**Step 3: Write implementation**

Create `backend/app/collectors/downloads.py`:

```python
"""Downloads collector — SABnzbd queue + Sonarr/Radarr import queues."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseCollector

logger = logging.getLogger(__name__)


class DownloadsCollector(BaseCollector):
    """Polls SABnzbd queue and Sonarr/Radarr import queues."""

    async def collect(self) -> None:
        data: dict[str, Any] = {
            "sabnzbd": {"speed": "", "sizeleft": "", "timeleft": "", "items": []},
            "sonarr_queue": [],
            "radarr_queue": [],
        }

        sab = self.clients.get("sabnzbd")
        if sab:
            try:
                raw = await sab.get_queue()
                q = raw.get("queue", {})
                data["sabnzbd"] = {
                    "speed": q.get("speed", ""),
                    "sizeleft": q.get("sizeleft", ""),
                    "timeleft": q.get("timeleft", ""),
                    "items": [
                        {
                            "name": s.get("filename", ""),
                            "percentage": s.get("percentage", "0"),
                            "sizeleft": s.get("sizeleft", ""),
                            "status": s.get("status", ""),
                            "timeleft": s.get("timeleft", ""),
                        }
                        for s in q.get("slots", [])
                    ],
                }
            except Exception:
                logger.exception("DownloadsCollector: SABnzbd failed")

        for svc_name in ("sonarr", "radarr"):
            client = self.clients.get(svc_name)
            if not client:
                continue
            try:
                raw = await client.get_queue()
                records = raw.get("records", [])
                data[f"{svc_name}_queue"] = [
                    {
                        "title": r.get("title", ""),
                        "status": r.get("status", ""),
                        "sizeleft": r.get("sizeleft", 0),
                        "size": r.get("size", 0),
                    }
                    for r in records
                ]
            except Exception:
                logger.exception("DownloadsCollector: %s failed", svc_name)

        await self.hub.broadcast("downloads", data)
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/collectors/test_downloads.py -v
```

Expected: 2 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/collectors/downloads.py backend/tests/collectors/test_downloads.py
git commit -m "feat: add downloads collector for SABnzbd + arr queues"
```

---

### Task 9: Streaming collector

**Files:**
- Create: `backend/app/collectors/streaming.py`
- Test: `backend/tests/collectors/test_streaming.py`

**Step 1: Write the failing test**

Create `backend/tests/collectors/test_streaming.py`:

```python
"""Tests for streaming collector."""

import pytest
from unittest.mock import AsyncMock
from app.collectors.streaming import StreamingCollector
from app.ws.hub import ConnectionHub


class TestStreamingCollector:

    @pytest.mark.asyncio
    async def test_collect_sessions(self):
        hub = ConnectionHub()
        plex = AsyncMock()
        plex.get_sessions.return_value = [
            {"User": {"title": "alice"}, "title": "Movie", "Media": [{"Part": [{"decision": "directplay"}]}]},
        ]
        plex.get_transcode_sessions.return_value = []

        collector = StreamingCollector(hub, {"plex": plex}, interval=15)
        await collector.collect()

        snapshot = hub.get_snapshot("streaming")
        assert snapshot["stream_count"] == 1
        assert snapshot["sessions"][0]["user"] == "alice"

    @pytest.mark.asyncio
    async def test_no_plex(self):
        hub = ConnectionHub()
        collector = StreamingCollector(hub, {}, interval=15)
        await collector.collect()
        snapshot = hub.get_snapshot("streaming")
        assert snapshot["stream_count"] == 0
```

**Step 2: Run test, then implement**

Create `backend/app/collectors/streaming.py`:

```python
"""Streaming collector — Plex active sessions."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseCollector

logger = logging.getLogger(__name__)


class StreamingCollector(BaseCollector):
    """Polls Plex for active streaming sessions."""

    async def collect(self) -> None:
        data: dict[str, Any] = {"stream_count": 0, "transcode_count": 0, "sessions": []}

        plex = self.clients.get("plex")
        if not plex:
            await self.hub.broadcast("streaming", data)
            return

        try:
            sessions = await plex.get_sessions()
            transcodes = await plex.get_transcode_sessions()

            parsed = []
            for s in sessions:
                user = s.get("User", {}).get("title", "Unknown")
                title = s.get("title", "Unknown")
                media = s.get("Media", [{}])
                decision = "directplay"
                if media:
                    parts = media[0].get("Part", [{}])
                    if parts:
                        decision = parts[0].get("decision", "directplay")
                parsed.append({
                    "user": user,
                    "title": title,
                    "decision": decision,
                    "grandparentTitle": s.get("grandparentTitle", ""),
                    "parentIndex": s.get("parentIndex", ""),
                    "index": s.get("index", ""),
                })

            data = {
                "stream_count": len(sessions),
                "transcode_count": len(transcodes),
                "sessions": parsed,
            }
        except Exception:
            logger.exception("StreamingCollector: Plex failed")

        await self.hub.broadcast("streaming", data)
```

**Step 3: Run tests and commit**

```bash
python -m pytest tests/collectors/test_streaming.py -v
git add backend/app/collectors/streaming.py backend/tests/collectors/test_streaming.py
git commit -m "feat: add streaming collector for Plex sessions"
```

---

### Task 10: Transcoding collector

**Files:**
- Create: `backend/app/collectors/transcoding.py`
- Test: `backend/tests/collectors/test_transcoding.py`

**Step 1: Write the failing test**

Create `backend/tests/collectors/test_transcoding.py`:

```python
"""Tests for transcoding collector."""

import pytest
from unittest.mock import AsyncMock
from app.collectors.transcoding import TranscodingCollector
from app.ws.hub import ConnectionHub


class TestTranscodingCollector:

    @pytest.mark.asyncio
    async def test_collect(self):
        hub = ConnectionHub()
        tdarr = AsyncMock()
        tdarr.get_status.return_value = {
            "nodes": {"node1": {"nodeName": "MainNode", "workers": {}}},
        }
        tdarr.get_statistics.return_value = {
            "totalFileCount": 1000,
            "totalTranscodeCount": 200,
            "sizeDiff": -5000000000,
        }
        tdarr.get_staged_files.return_value = [{"_id": "1"}, {"_id": "2"}]

        collector = TranscodingCollector(hub, {"tdarr": tdarr}, interval=30)
        await collector.collect()

        snapshot = hub.get_snapshot("transcoding")
        assert snapshot["queue_size"] == 2
        assert snapshot["total_files"] == 1000

    @pytest.mark.asyncio
    async def test_no_tdarr(self):
        hub = ConnectionHub()
        collector = TranscodingCollector(hub, {}, interval=30)
        await collector.collect()
        snapshot = hub.get_snapshot("transcoding")
        assert snapshot["queue_size"] == 0
```

**Step 2: Write implementation**

Create `backend/app/collectors/transcoding.py`:

```python
"""Transcoding collector — Tdarr pipeline status."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseCollector

logger = logging.getLogger(__name__)


class TranscodingCollector(BaseCollector):
    """Polls Tdarr for node status, queue depth, and statistics."""

    async def collect(self) -> None:
        data: dict[str, Any] = {
            "nodes": [],
            "queue_size": 0,
            "total_files": 0,
            "total_transcodes": 0,
            "size_diff_bytes": 0,
        }

        tdarr = self.clients.get("tdarr")
        if not tdarr:
            await self.hub.broadcast("transcoding", data)
            return

        try:
            status = await tdarr.get_status()
            stats = await tdarr.get_statistics()
            staged = await tdarr.get_staged_files()

            nodes = []
            for nid, ndata in status.get("nodes", {}).items():
                nodes.append({
                    "id": nid,
                    "name": ndata.get("nodeName", nid),
                    "workers": ndata.get("workers", {}),
                })

            queue_size = len(staged) if isinstance(staged, list) else 0

            total_files = 0
            total_transcodes = 0
            size_diff = 0
            if isinstance(stats, dict):
                total_files = stats.get("totalFileCount", 0)
                total_transcodes = stats.get("totalTranscodeCount", 0)
                size_diff = stats.get("sizeDiff", 0)

            data = {
                "nodes": nodes,
                "queue_size": queue_size,
                "total_files": total_files,
                "total_transcodes": total_transcodes,
                "size_diff_bytes": size_diff,
            }
        except Exception:
            logger.exception("TranscodingCollector: Tdarr failed")

        await self.hub.broadcast("transcoding", data)
```

**Step 3: Run tests and commit**

```bash
python -m pytest tests/collectors/test_transcoding.py -v
git add backend/app/collectors/transcoding.py backend/tests/collectors/test_transcoding.py
git commit -m "feat: add transcoding collector for Tdarr pipeline"
```

---

### Task 11: Calendar collector

**Files:**
- Create: `backend/app/collectors/calendar.py`
- Test: `backend/tests/collectors/test_calendar.py`

**Step 1: Write the failing test**

Create `backend/tests/collectors/test_calendar.py`:

```python
"""Tests for calendar collector."""

import pytest
from unittest.mock import AsyncMock
from app.collectors.calendar import CalendarCollector
from app.ws.hub import ConnectionHub


class TestCalendarCollector:

    @pytest.mark.asyncio
    async def test_collect_episodes_and_movies(self):
        hub = ConnectionHub()
        sonarr = AsyncMock()
        sonarr.get_calendar.return_value = [
            {"seriesTitle": "Show", "title": "Ep1", "airDateUtc": "2026-02-20T20:00:00Z",
             "seasonNumber": 1, "episodeNumber": 1, "hasFile": False},
        ]
        radarr = AsyncMock()
        radarr.get_calendar.return_value = [
            {"title": "Movie", "inCinemas": "2026-03-01", "hasFile": False},
        ]

        collector = CalendarCollector(hub, {"sonarr": sonarr, "radarr": radarr}, interval=300)
        await collector.collect()

        snapshot = hub.get_snapshot("calendar")
        assert len(snapshot["episodes"]) == 1
        assert len(snapshot["movies"]) == 1

    @pytest.mark.asyncio
    async def test_collect_no_services(self):
        hub = ConnectionHub()
        collector = CalendarCollector(hub, {}, interval=300)
        await collector.collect()
        snapshot = hub.get_snapshot("calendar")
        assert snapshot["episodes"] == []
        assert snapshot["movies"] == []
```

**Step 2: Write implementation**

Create `backend/app/collectors/calendar.py`:

```python
"""Calendar collector — upcoming episodes and movies from Sonarr/Radarr."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from .base import BaseCollector

logger = logging.getLogger(__name__)


class CalendarCollector(BaseCollector):
    """Polls Sonarr/Radarr calendars for upcoming media."""

    async def collect(self) -> None:
        data: dict[str, Any] = {"episodes": [], "movies": []}
        now = datetime.now(timezone.utc)
        start = now.isoformat()
        end = (now + timedelta(days=7)).isoformat()

        sonarr = self.clients.get("sonarr")
        if sonarr:
            try:
                eps = await sonarr.get_calendar(start=start, end=end)
                data["episodes"] = [
                    {
                        "series": e.get("seriesTitle", ""),
                        "title": e.get("title", ""),
                        "airDate": e.get("airDateUtc", ""),
                        "season": e.get("seasonNumber", 0),
                        "episode": e.get("episodeNumber", 0),
                        "hasFile": e.get("hasFile", False),
                    }
                    for e in eps
                ]
            except Exception:
                logger.exception("CalendarCollector: Sonarr failed")

        radarr = self.clients.get("radarr")
        if radarr:
            try:
                movies = await radarr.get_calendar(start=start, end=end)
                data["movies"] = [
                    {
                        "title": m.get("title", ""),
                        "releaseDate": m.get("inCinemas", m.get("digitalRelease", "")),
                        "hasFile": m.get("hasFile", False),
                    }
                    for m in movies
                ]
            except Exception:
                logger.exception("CalendarCollector: Radarr failed")

        await self.hub.broadcast("calendar", data)
```

**Step 3: Run tests and commit**

```bash
python -m pytest tests/collectors/test_calendar.py -v
git add backend/app/collectors/calendar.py backend/tests/collectors/test_calendar.py
git commit -m "feat: add calendar collector for upcoming media"
```

---

### Task 12: REST routers

**Files:**
- Create: `backend/app/routers/health.py`
- Create: `backend/app/routers/downloads.py`
- Create: `backend/app/routers/streaming.py`
- Create: `backend/app/routers/transcoding.py`
- Create: `backend/app/routers/calendar.py`

**Step 1: Write all routers**

Each router is a thin GET endpoint that returns the latest snapshot from the hub. These are simple enough to write together.

Create `backend/app/routers/health.py`:

```python
"""GET /api/health — latest service health snapshot."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/health")
async def get_health(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("health") or {"services": []}
```

Create `backend/app/routers/downloads.py`:

```python
"""GET /api/downloads — latest download queue snapshot."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/downloads")
async def get_downloads(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("downloads") or {"sabnzbd": {"items": []}, "sonarr_queue": [], "radarr_queue": []}
```

Create `backend/app/routers/streaming.py`:

```python
"""GET /api/streaming — latest Plex streaming snapshot."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/streaming")
async def get_streaming(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("streaming") or {"stream_count": 0, "transcode_count": 0, "sessions": []}
```

Create `backend/app/routers/transcoding.py`:

```python
"""GET /api/transcoding — latest Tdarr transcode snapshot."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/transcoding")
async def get_transcoding(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("transcoding") or {"nodes": [], "queue_size": 0}
```

Create `backend/app/routers/calendar.py`:

```python
"""GET /api/calendar — latest upcoming media snapshot."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/calendar")
async def get_calendar(request: Request):
    hub = request.app.state.hub
    return hub.get_snapshot("calendar") or {"episodes": [], "movies": []}
```

**Step 2: Commit**

```bash
git add backend/app/routers/
git commit -m "feat: add REST routers for all dashboard endpoints"
```

---

### Task 13: Prometheus metrics endpoint

**Files:**
- Create: `backend/app/metrics.py`

**Step 1: Write implementation**

Create `backend/app/metrics.py`:

```python
"""Prometheus metrics exposition — reads from hub snapshots."""

from __future__ import annotations

from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Request, Response

router = APIRouter()

# Gauges
service_up = Gauge("mcc_service_up", "Service online status", ["service"])
service_latency = Gauge("mcc_service_latency_seconds", "Service response time", ["service"])
downloads_active = Gauge("mcc_downloads_active", "Active downloads")
downloads_speed = Gauge("mcc_downloads_speed_bytes", "Download speed in bytes/s")
plex_streams = Gauge("mcc_plex_streams_active", "Active Plex streams")
plex_transcodes = Gauge("mcc_plex_transcode_active", "Active Plex transcodes")
tdarr_queue = Gauge("mcc_tdarr_queue_size", "Tdarr pending queue size")
tdarr_space_saved = Gauge("mcc_tdarr_space_saved_bytes", "Tdarr cumulative space savings")


def update_metrics_from_hub(hub) -> None:
    """Read hub snapshots and update Prometheus gauges."""
    health = hub.get_snapshot("health")
    if health:
        for svc in health.get("services", []):
            service_up.labels(service=svc["name"]).set(1 if svc["status"] == "online" else 0)
            service_latency.labels(service=svc["name"]).set(svc.get("response_ms", 0) / 1000)

    dl = hub.get_snapshot("downloads")
    if dl:
        items = dl.get("sabnzbd", {}).get("items", [])
        downloads_active.set(len(items))

    streaming = hub.get_snapshot("streaming")
    if streaming:
        plex_streams.set(streaming.get("stream_count", 0))
        plex_transcodes.set(streaming.get("transcode_count", 0))

    transcoding = hub.get_snapshot("transcoding")
    if transcoding:
        tdarr_queue.set(transcoding.get("queue_size", 0))
        tdarr_space_saved.set(abs(transcoding.get("size_diff_bytes", 0)))


@router.get("/metrics")
async def metrics(request: Request):
    update_metrics_from_hub(request.app.state.hub)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Step 2: Commit**

```bash
git add backend/app/metrics.py
git commit -m "feat: add Prometheus metrics endpoint"
```

---

### Task 14: FastAPI main app with lifespan

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_main.py`

**Step 1: Write the failing test**

Create `backend/tests/test_main.py`:

```python
"""Tests for FastAPI app startup."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


class TestApp:

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        app = create_app(skip_collectors=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/health")
        assert r.status_code == 200
        assert "services" in r.json()

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        app = create_app(skip_collectors=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/metrics")
        assert r.status_code == 200
        assert b"mcc_service_up" in r.content
```

**Step 2: Write implementation**

Create `backend/app/main.py`:

```python
"""FastAPI application — lifespan manages service clients and collectors."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .ws.hub import ConnectionHub
from .collectors.health import HealthCollector
from .collectors.downloads import DownloadsCollector
from .collectors.streaming import StreamingCollector
from .collectors.transcoding import TranscodingCollector
from .collectors.calendar import CalendarCollector
from .routers import health, downloads, streaming, transcoding, calendar
from .metrics import router as metrics_router

# Service client imports
from .services.sonarr import SonarrClient
from .services.radarr import RadarrClient
from .services.prowlarr import ProwlarrClient
from .services.bazarr import BazarrClient
from .services.overseerr import OverseerrClient
from .services.plex import PlexClient
from .services.tdarr import TdarrClient
from .services.sabnzbd import SABnzbdClient
from .services.unpackerr import UnpackerrClient

logger = logging.getLogger(__name__)

# Client factory registry
CLIENT_FACTORIES = {
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


def _build_clients(settings: Settings) -> dict:
    clients = {}
    for name in settings.configured_services():
        factory = CLIENT_FACTORIES.get(name)
        if factory:
            clients[name] = factory(settings)
            logger.info("Initialized client: %s", name)
    return clients


def create_app(skip_collectors: bool = False) -> FastAPI:
    settings = Settings()
    hub = ConnectionHub()
    clients = _build_clients(settings)
    collectors = []

    if not skip_collectors:
        collectors = [
            HealthCollector(hub, clients, interval=30),
            DownloadsCollector(hub, clients, interval=10),
            StreamingCollector(hub, clients, interval=15),
            TranscodingCollector(hub, clients, interval=30),
            CalendarCollector(hub, clients, interval=300),
        ]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        for c in collectors:
            c.start()
        logger.info("MCC started — %d services, %d collectors", len(clients), len(collectors))
        yield
        for c in collectors:
            await c.stop()
        for client in clients.values():
            await client.close()
        logger.info("MCC shutdown complete")

    app = FastAPI(title="Media Command Center", lifespan=lifespan)
    app.state.hub = hub
    app.state.clients = clients

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    app.include_router(health.router)
    app.include_router(downloads.router)
    app.include_router(streaming.router)
    app.include_router(transcoding.router)
    app.include_router(calendar.router)
    app.include_router(metrics_router)

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        hub.connect(ws)
        # Send current snapshots on connect
        for msg_type in ("health", "downloads", "streaming", "transcoding", "calendar"):
            snapshot = hub.get_snapshot(msg_type)
            if snapshot:
                import json
                from datetime import datetime, timezone
                await ws.send_text(json.dumps({
                    "type": msg_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": snapshot,
                }))
        try:
            while True:
                await ws.receive_text()  # Keep alive
        except WebSocketDisconnect:
            hub.disconnect(ws)

    return app


# Entry point for uvicorn
app = create_app()
```

**Step 3: Run tests**

```bash
python -m pytest tests/test_main.py -v
```

Expected: 2 tests PASS.

**Step 4: Commit**

```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat: add FastAPI main app with lifespan, WS endpoint, client factories"
```

---

## Phase 2: Frontend

### Task 15: Initialize frontend with Vite + React + TypeScript + Tailwind + shadcn/ui

**Step 1: Scaffold the project**

```bash
cd C:\Users\Shikyo\media-command-center
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install zustand recharts
```

**Step 2: Configure Tailwind**

Edit `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8880',
      '/ws': { target: 'ws://localhost:8880', ws: true },
      '/metrics': 'http://localhost:8880',
    },
  },
})
```

Replace `frontend/src/index.css` with:

```css
@import "tailwindcss";
```

**Step 3: Initialize shadcn/ui**

```bash
cd C:\Users\Shikyo\media-command-center\frontend
npx shadcn@latest init
```

Select: New York style, Zinc base color, CSS variables: yes.

**Step 4: Add needed shadcn components**

```bash
npx shadcn@latest add card badge scroll-area separator
```

**Step 5: Commit**

```bash
cd C:\Users\Shikyo\media-command-center
git add frontend/
git commit -m "feat: scaffold frontend with Vite + React + Tailwind + shadcn/ui"
```

---

### Task 16: Design system — glassmorphism globals

**Files:**
- Modify: `frontend/src/index.css`

**Step 1: Write the glassmorphism design tokens and utilities**

Replace `frontend/src/index.css`:

```css
@import "tailwindcss";

@theme {
  /* Glassmorphism Cyberpunk Design Tokens */
  --color-bg-base: #0a0a0f;
  --color-surface: rgba(255, 255, 255, 0.05);
  --color-surface-hover: rgba(255, 255, 255, 0.08);
  --color-border: rgba(255, 255, 255, 0.10);
  --color-glow-primary: #00d4ff;
  --color-glow-success: #00ff88;
  --color-glow-warning: #ffaa00;
  --color-glow-danger: #ff3366;
  --color-glow-info: #7c5cfc;
  --color-text-primary: #e4e4e7;
  --color-text-secondary: #a1a1aa;
  --color-text-muted: #71717a;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

/* Base styles */
body {
  background-color: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  min-height: 100vh;
}

/* Glassmorphic card utility */
.glass-card {
  background: var(--color-surface);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.glass-card:hover {
  background: var(--color-surface-hover);
}

/* Status glow variants */
.glow-primary { box-shadow: 0 0 20px rgba(0, 212, 255, 0.15), inset 0 0 20px rgba(0, 212, 255, 0.05); }
.glow-success { box-shadow: 0 0 20px rgba(0, 255, 136, 0.15), inset 0 0 20px rgba(0, 255, 136, 0.05); }
.glow-warning { box-shadow: 0 0 20px rgba(255, 170, 0, 0.15), inset 0 0 20px rgba(255, 170, 0, 0.05); }
.glow-danger  { box-shadow: 0 0 20px rgba(255, 51, 102, 0.15), inset 0 0 20px rgba(255, 51, 102, 0.05); }
.glow-info    { box-shadow: 0 0 20px rgba(124, 92, 252, 0.15), inset 0 0 20px rgba(124, 92, 252, 0.05); }

/* Pulsing status dot */
@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-dot-online  { background: var(--color-glow-success); box-shadow: 0 0 8px var(--color-glow-success); }
.status-dot-offline { background: var(--color-glow-danger);  box-shadow: 0 0 8px var(--color-glow-danger); }
.status-dot-warning { background: var(--color-glow-warning); box-shadow: 0 0 8px var(--color-glow-warning); }

/* Progress bar */
.progress-bar {
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--color-glow-primary), var(--color-glow-info));
  transition: width 0.5s ease;
  position: relative;
}

/* Shimmer animation for active progress */
.progress-bar-fill.active::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Fade-in stagger animation */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fade-in-up 0.4s ease-out forwards;
  opacity: 0;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
```

**Step 2: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: add glassmorphism cyberpunk design system"
```

---

### Task 17: TypeScript types

**Files:**
- Create: `frontend/src/lib/types.ts`

**Step 1: Write types matching backend models**

Create `frontend/src/lib/types.ts`:

```typescript
/* Types matching backend WebSocket message shapes. */

export interface WsMessage<T = unknown> {
  type: 'health' | 'downloads' | 'streaming' | 'transcoding' | 'calendar'
  timestamp: string
  data: T
}

/* Health */
export interface ServiceHealth {
  name: string
  status: 'online' | 'offline'
  version: string
  response_ms: number
}

export interface HealthData {
  services: ServiceHealth[]
}

/* Downloads */
export interface SabItem {
  name: string
  percentage: string
  sizeleft: string
  status: string
  timeleft: string
}

export interface DownloadsData {
  sabnzbd: {
    speed: string
    sizeleft: string
    timeleft: string
    items: SabItem[]
  }
  sonarr_queue: { title: string; status: string; sizeleft: number; size: number }[]
  radarr_queue: { title: string; status: string; sizeleft: number; size: number }[]
}

/* Streaming */
export interface PlexSession {
  user: string
  title: string
  decision: string
  grandparentTitle: string
  parentIndex: string
  index: string
}

export interface StreamingData {
  stream_count: number
  transcode_count: number
  sessions: PlexSession[]
}

/* Transcoding */
export interface TdarrNode {
  id: string
  name: string
  workers: Record<string, unknown>
}

export interface TranscodingData {
  nodes: TdarrNode[]
  queue_size: number
  total_files: number
  total_transcodes: number
  size_diff_bytes: number
}

/* Calendar */
export interface CalendarEpisode {
  series: string
  title: string
  airDate: string
  season: number
  episode: number
  hasFile: boolean
}

export interface CalendarMovie {
  title: string
  releaseDate: string
  hasFile: boolean
}

export interface CalendarData {
  episodes: CalendarEpisode[]
  movies: CalendarMovie[]
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat: add TypeScript types matching backend WS models"
```

---

### Task 18: Zustand stores

**Files:**
- Create: `frontend/src/hooks/useStore.ts`

**Step 1: Write Zustand stores**

Create `frontend/src/hooks/useStore.ts`:

```typescript
import { create } from 'zustand'
import type { HealthData, DownloadsData, StreamingData, TranscodingData, CalendarData } from '@/lib/types'

interface HealthStore {
  data: HealthData
  setData: (d: HealthData) => void
}

export const useHealthStore = create<HealthStore>((set) => ({
  data: { services: [] },
  setData: (data) => set({ data }),
}))

interface DownloadsStore {
  data: DownloadsData
  setData: (d: DownloadsData) => void
}

export const useDownloadsStore = create<DownloadsStore>((set) => ({
  data: { sabnzbd: { speed: '', sizeleft: '', timeleft: '', items: [] }, sonarr_queue: [], radarr_queue: [] },
  setData: (data) => set({ data }),
}))

interface StreamingStore {
  data: StreamingData
  setData: (d: StreamingData) => void
}

export const useStreamingStore = create<StreamingStore>((set) => ({
  data: { stream_count: 0, transcode_count: 0, sessions: [] },
  setData: (data) => set({ data }),
}))

interface TranscodingStore {
  data: TranscodingData
  setData: (d: TranscodingData) => void
}

export const useTranscodingStore = create<TranscodingStore>((set) => ({
  data: { nodes: [], queue_size: 0, total_files: 0, total_transcodes: 0, size_diff_bytes: 0 },
  setData: (data) => set({ data }),
}))

interface CalendarStore {
  data: CalendarData
  setData: (d: CalendarData) => void
}

export const useCalendarStore = create<CalendarStore>((set) => ({
  data: { episodes: [], movies: [] },
  setData: (data) => set({ data }),
}))
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useStore.ts
git commit -m "feat: add Zustand stores for all dashboard domains"
```

---

### Task 19: WebSocket hook with auto-reconnect

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`

**Step 1: Write the hook**

Create `frontend/src/hooks/useWebSocket.ts`:

```typescript
import { useEffect, useRef } from 'react'
import type { WsMessage } from '@/lib/types'
import {
  useHealthStore,
  useDownloadsStore,
  useStreamingStore,
  useTranscodingStore,
  useCalendarStore,
} from './useStore'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data)
          switch (msg.type) {
            case 'health':
              useHealthStore.getState().setData(msg.data as any)
              break
            case 'downloads':
              useDownloadsStore.getState().setData(msg.data as any)
              break
            case 'streaming':
              useStreamingStore.getState().setData(msg.data as any)
              break
            case 'transcoding':
              useTranscodingStore.getState().setData(msg.data as any)
              break
            case 'calendar':
              useCalendarStore.getState().setData(msg.data as any)
              break
          }
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onclose = () => {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [])
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts
git commit -m "feat: add WebSocket hook with auto-reconnect"
```

---

### Task 20: Utility functions

**Files:**
- Create: `frontend/src/lib/utils.ts`

**Step 1: Write utility functions**

Create `frontend/src/lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

export function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}h ${m % 60}m`
  if (m > 0) return `${m}m ${s % 60}s`
  return `${s}s`
}

export function relativeTime(isoDate: string): string {
  const now = new Date()
  const date = new Date(isoDate)
  const diffMs = date.getTime() - now.getTime()
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Tomorrow'
  if (diffDays > 0) return `In ${diffDays} days`
  return `${Math.abs(diffDays)} days ago`
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/utils.ts
git commit -m "feat: add utility functions for formatting"
```

---

### Task 21: Layout shell — sidebar + header

**Files:**
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Shell.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write layout components**

Create `frontend/src/components/layout/Sidebar.tsx`:

```tsx
import {
  Activity,
  Download,
  Tv,
  HardDrive,
  Calendar,
} from 'lucide-react'

const NAV_ITEMS = [
  { icon: Activity, label: 'Overview', id: 'overview' },
  { icon: Download, label: 'Downloads', id: 'downloads' },
  { icon: Tv, label: 'Plex', id: 'streaming' },
  { icon: HardDrive, label: 'Tdarr', id: 'transcoding' },
  { icon: Calendar, label: 'Calendar', id: 'calendar' },
] as const

interface SidebarProps {
  active: string
  onNavigate: (id: string) => void
}

export function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-16 glass-card rounded-none border-r border-t-0 border-b-0 border-l-0 flex flex-col items-center py-6 gap-2 z-50">
      <div className="text-glow-primary font-mono text-xs font-bold mb-6">MCC</div>
      {NAV_ITEMS.map(({ icon: Icon, label, id }) => (
        <button
          key={id}
          onClick={() => onNavigate(id)}
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            active === id
              ? 'bg-[rgba(0,212,255,0.15)] text-glow-primary'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
          }`}
          title={label}
        >
          <Icon size={20} />
        </button>
      ))}
    </aside>
  )
}
```

Install lucide-react:

```bash
cd C:\Users\Shikyo\media-command-center\frontend
npm install lucide-react
```

Create `frontend/src/components/layout/Shell.tsx`:

```tsx
import { useState, type ReactNode } from 'react'
import { Sidebar } from './Sidebar'

interface ShellProps {
  children: (activeView: string) => ReactNode
}

export function Shell({ children }: ShellProps) {
  const [active, setActive] = useState('overview')

  return (
    <div className="min-h-screen bg-bg-base">
      <Sidebar active={active} onNavigate={setActive} />
      <main className="ml-16 p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-text-primary">
            Media Command Center
          </h1>
          <p className="text-sm text-text-muted">Real-time media infrastructure monitoring</p>
        </header>
        {children(active)}
      </main>
    </div>
  )
}
```

Replace `frontend/src/App.tsx`:

```tsx
import { useWebSocket } from '@/hooks/useWebSocket'
import { Shell } from '@/components/layout/Shell'
import { HealthGrid } from '@/components/panels/HealthGrid'
import { DownloadsPanel } from '@/components/panels/DownloadsPanel'
import { StreamingPanel } from '@/components/panels/StreamingPanel'
import { TranscodingPanel } from '@/components/panels/TranscodingPanel'
import { CalendarPanel } from '@/components/panels/CalendarPanel'

export default function App() {
  useWebSocket()

  return (
    <Shell>
      {(view) => (
        <>
          {(view === 'overview' || view === 'health') && <HealthGrid />}
          {(view === 'overview' || view === 'downloads') && <DownloadsPanel />}
          {(view === 'overview' || view === 'streaming') && <StreamingPanel />}
          {(view === 'overview' || view === 'transcoding') && <TranscodingPanel />}
          {(view === 'overview' || view === 'calendar') && <CalendarPanel />}
        </>
      )}
    </Shell>
  )
}
```

**Step 2: Commit** (after panels exist — see next tasks)

---

### Task 22: Service Health Grid panel

**Files:**
- Create: `frontend/src/components/panels/HealthGrid.tsx`

**Step 1: Write the component**

Create `frontend/src/components/panels/HealthGrid.tsx`:

```tsx
import { useHealthStore } from '@/hooks/useStore'

const SERVICE_URLS: Record<string, string> = {
  sonarr: '/sonarr',
  radarr: '/radarr',
  prowlarr: '/prowlarr',
  bazarr: '/bazarr',
  overseerr: '/overseerr',
  plex: '/plex',
  tdarr: '/tdarr',
  sabnzbd: '/sabnzbd',
  unpackerr: '/unpackerr',
}

export function HealthGrid() {
  const { services } = useHealthStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Service Health</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {services.map((svc, i) => (
          <a
            key={svc.name}
            href={SERVICE_URLS[svc.name] || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className={`glass-card p-4 animate-fade-in cursor-pointer transition-all ${
              svc.status === 'online' ? 'glow-success' : 'glow-danger'
            }`}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`status-dot ${svc.status === 'online' ? 'status-dot-online' : 'status-dot-offline'}`} />
              <span className="text-sm font-medium capitalize">{svc.name}</span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-text-muted font-mono">
                {svc.version || '—'}
              </span>
              <span className="text-xs text-text-muted font-mono">
                {svc.response_ms}ms
              </span>
            </div>
          </a>
        ))}
        {services.length === 0 && (
          <div className="glass-card p-4 col-span-full text-center text-text-muted">
            No services configured
          </div>
        )}
      </div>
    </section>
  )
}
```

---

### Task 23: Active Downloads panel

**Files:**
- Create: `frontend/src/components/panels/DownloadsPanel.tsx`

Create `frontend/src/components/panels/DownloadsPanel.tsx`:

```tsx
import { useDownloadsStore } from '@/hooks/useStore'

export function DownloadsPanel() {
  const { sabnzbd, sonarr_queue, radarr_queue } = useDownloadsStore((s) => s.data)
  const hasItems = sabnzbd.items.length > 0 || sonarr_queue.length > 0 || radarr_queue.length > 0

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Active Downloads</h2>
        {sabnzbd.speed && (
          <span className="text-sm font-mono text-glow-primary">{sabnzbd.speed}/s</span>
        )}
      </div>

      <div className="glass-card p-4 glow-primary">
        {!hasItems && (
          <p className="text-text-muted text-sm text-center py-4">No active downloads</p>
        )}

        {sabnzbd.items.map((item, i) => (
          <div key={i} className="mb-4 last:mb-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-text-primary truncate mr-4">{item.name}</span>
              <span className="text-xs font-mono text-text-secondary shrink-0">
                {item.percentage}% &middot; {item.timeleft}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className={`progress-bar-fill ${item.status === 'Downloading' ? 'active' : ''}`}
                style={{ width: `${item.percentage}%` }}
              />
            </div>
          </div>
        ))}

        {(sonarr_queue.length > 0 || radarr_queue.length > 0) && sabnzbd.items.length > 0 && (
          <hr className="border-border my-4" />
        )}

        {[...sonarr_queue, ...radarr_queue].map((item, i) => (
          <div key={`q-${i}`} className="flex items-center justify-between py-1">
            <span className="text-sm text-text-secondary truncate mr-4">{item.title}</span>
            <span className="text-xs font-mono text-text-muted">{item.status}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
```

---

### Task 24: Plex Streaming Activity panel

**Files:**
- Create: `frontend/src/components/panels/StreamingPanel.tsx`

Create `frontend/src/components/panels/StreamingPanel.tsx`:

```tsx
import { useStreamingStore } from '@/hooks/useStore'

export function StreamingPanel() {
  const { stream_count, transcode_count, sessions } = useStreamingStore((s) => s.data)

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Plex Streaming</h2>
        <div className="flex gap-4 text-sm font-mono">
          <span className="text-glow-success">{stream_count} stream{stream_count !== 1 ? 's' : ''}</span>
          {transcode_count > 0 && (
            <span className="text-glow-warning">{transcode_count} transcode{transcode_count !== 1 ? 's' : ''}</span>
          )}
        </div>
      </div>

      <div className="glass-card p-4 glow-info">
        {sessions.length === 0 && (
          <p className="text-text-muted text-sm text-center py-4">No active streams</p>
        )}

        <div className="space-y-3">
          {sessions.map((s, i) => {
            const mediaTitle = s.grandparentTitle
              ? `${s.grandparentTitle} — S${s.parentIndex}E${s.index}`
              : s.title

            return (
              <div key={i} className="flex items-center justify-between animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center text-xs font-mono text-glow-primary">
                    {s.user.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm text-text-primary">{mediaTitle}</p>
                    <p className="text-xs text-text-muted">{s.user}</p>
                  </div>
                </div>
                <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                  s.decision === 'directplay' ? 'bg-[rgba(0,255,136,0.1)] text-glow-success'
                    : 'bg-[rgba(255,170,0,0.1)] text-glow-warning'
                }`}>
                  {s.decision === 'directplay' ? 'Direct Play' : 'Transcode'}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
```

---

### Task 25: Tdarr Transcode Pipeline panel

**Files:**
- Create: `frontend/src/components/panels/TranscodingPanel.tsx`

Create `frontend/src/components/panels/TranscodingPanel.tsx`:

```tsx
import { useTranscodingStore } from '@/hooks/useStore'
import { formatBytes } from '@/lib/utils'

export function TranscodingPanel() {
  const { nodes, queue_size, total_files, total_transcodes, size_diff_bytes } = useTranscodingStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Tdarr Transcode Pipeline</h2>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {[
          { label: 'Queue', value: queue_size, glow: queue_size > 0 ? 'text-glow-warning' : 'text-glow-success' },
          { label: 'Total Files', value: total_files.toLocaleString(), glow: 'text-glow-primary' },
          { label: 'Transcoded', value: total_transcodes.toLocaleString(), glow: 'text-glow-info' },
          { label: 'Space Saved', value: formatBytes(Math.abs(size_diff_bytes)), glow: 'text-glow-success' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card p-3 text-center">
            <p className={`text-xl font-mono font-bold ${stat.glow}`}>{stat.value}</p>
            <p className="text-xs text-text-muted">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Nodes */}
      <div className="glass-card p-4 glow-info">
        {nodes.length === 0 && (
          <p className="text-text-muted text-sm text-center py-4">No Tdarr nodes connected</p>
        )}
        {nodes.map((node) => {
          const workerCount = Object.keys(node.workers).length
          return (
            <div key={node.id} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <span className="status-dot status-dot-online" />
                <span className="text-sm">{node.name}</span>
              </div>
              <span className="text-xs font-mono text-text-muted">
                {workerCount} worker{workerCount !== 1 ? 's' : ''}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
```

---

### Task 26: Upcoming Calendar panel

**Files:**
- Create: `frontend/src/components/panels/CalendarPanel.tsx`

Create `frontend/src/components/panels/CalendarPanel.tsx`:

```tsx
import { useCalendarStore } from '@/hooks/useStore'
import { relativeTime } from '@/lib/utils'

export function CalendarPanel() {
  const { episodes, movies } = useCalendarStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Upcoming</h2>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Episodes */}
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-glow-primary mb-3">Episodes</h3>
          {episodes.length === 0 && <p className="text-text-muted text-sm">Nothing upcoming</p>}
          <div className="space-y-2">
            {episodes.map((ep, i) => (
              <div key={i} className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-primary">{ep.series}</p>
                  <p className="text-xs text-text-muted">
                    S{String(ep.season).padStart(2, '0')}E{String(ep.episode).padStart(2, '0')} — {ep.title}
                  </p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-xs font-mono text-text-secondary">{relativeTime(ep.airDate)}</p>
                  {ep.hasFile && <span className="text-xs text-glow-success">Downloaded</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Movies */}
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-glow-info mb-3">Movies</h3>
          {movies.length === 0 && <p className="text-text-muted text-sm">Nothing upcoming</p>}
          <div className="space-y-2">
            {movies.map((m, i) => (
              <div key={i} className="flex items-center justify-between">
                <p className="text-sm text-text-primary">{m.title}</p>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-xs font-mono text-text-secondary">{relativeTime(m.releaseDate)}</p>
                  {m.hasFile && <span className="text-xs text-glow-success">Downloaded</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
```

**Commit all panels + layout**

```bash
git add frontend/src/
git commit -m "feat: add all dashboard panels and layout shell"
```

---

## Phase 3: Docker Deployment

### Task 27: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/

EXPOSE 8880

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8880"]
```

---

### Task 28: Frontend Dockerfile

**Files:**
- Create: `frontend/Dockerfile`

Create `frontend/Dockerfile`:

```dockerfile
FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8880;
    }

    location /ws {
        proxy_pass http://backend:8880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /metrics {
        proxy_pass http://backend:8880;
    }
}
```

---

### Task 29: Docker Compose

**Files:**
- Create: `docker-compose.yml`

Create `docker-compose.yml`:

```yaml
services:
  backend:
    build: ./backend
    env_file: ./backend/.env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "${MCC_PORT:-8880}:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**Commit deployment files**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml
git commit -m "feat: add Docker deployment (backend + frontend + compose)"
```

---

### Task 30: Run all backend tests

```bash
cd C:\Users\Shikyo\media-command-center\backend
python -m pytest tests/ -v
```

Expected: All tests PASS.

---

### Task 31: Run frontend dev build

```bash
cd C:\Users\Shikyo\media-command-center\frontend
npm run build
```

Expected: Build completes successfully.

**Final commit:**

```bash
cd C:\Users\Shikyo\media-command-center
git add -A
git commit -m "chore: finalize Media Command Center v0.1.0"
```

---

## Verification Checklist

1. **Backend tests pass**: `cd backend && python -m pytest tests/ -v`
2. **Frontend builds**: `cd frontend && npm run build`
3. **Backend starts**: `cd backend && uvicorn app.main:app --port 8880` — visit `http://localhost:8880/api/health`
4. **Frontend dev**: `cd frontend && npm run dev` — visit `http://localhost:5173`
5. **WebSocket connects**: Browser console should show WS messages arriving
6. **Prometheus metrics**: `curl http://localhost:8880/metrics` — should show `mcc_*` gauges
7. **Docker**: `docker-compose up --build` — visit `http://localhost:8880`
