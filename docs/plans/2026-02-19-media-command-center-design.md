# Media Command Center — Design Document

**Date:** 2026-02-19
**Status:** Approved

## Overview

A standalone, open-source web dashboard for monitoring a media server stack (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, Plex, Tdarr, SABnzbd, Unpackerr, Recyclarr). Provides a unified command center with real-time service health, download progress, Plex streaming activity, Tdarr transcode pipeline, and upcoming media calendar.

Complements Homarr (navigation/links) by providing **visibility and live status** across the entire stack.

## Architecture

**Monorepo** with `backend/` and `frontend/` directories.

- **Backend:** Python FastAPI with its own service clients (httpx). No MCP dependency — fully standalone.
- **Frontend:** React + Vite + Tailwind CSS + shadcn/ui
- **Live updates:** WebSocket push from backend collectors to frontend Zustand stores
- **Metrics export:** Prometheus `/metrics` endpoint for Grafana integration
- **Deployment:** Docker Compose (backend + frontend containers)

### Project Structure

```
media-command-center/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, CORS
│   │   ├── config.py            # Pydantic Settings from .env
│   │   ├── services/            # Thin API clients (one per service)
│   │   │   ├── base.py          # Shared httpx client with retry logic
│   │   │   ├── sonarr.py
│   │   │   ├── radarr.py
│   │   │   ├── prowlarr.py
│   │   │   ├── bazarr.py
│   │   │   ├── overseerr.py
│   │   │   ├── plex.py
│   │   │   ├── tdarr.py
│   │   │   ├── sabnzbd.py
│   │   │   └── unpackerr.py
│   │   ├── collectors/          # Background pollers that push to WS hub
│   │   │   ├── base.py          # BaseCollector with interval loop + error handling
│   │   │   ├── health.py        # All services health (30s)
│   │   │   ├── downloads.py     # SABnzbd + Sonarr/Radarr queues (10s)
│   │   │   ├── streaming.py     # Plex sessions (15s)
│   │   │   ├── transcoding.py   # Tdarr pipeline (30s)
│   │   │   └── calendar.py      # Upcoming episodes/movies (5m)
│   │   ├── ws/
│   │   │   └── hub.py           # WebSocket connection manager + broadcast
│   │   ├── routers/
│   │   │   ├── health.py        # GET /api/health
│   │   │   ├── downloads.py     # GET /api/downloads
│   │   │   ├── streaming.py     # GET /api/streaming
│   │   │   ├── transcoding.py   # GET /api/transcoding
│   │   │   └── calendar.py      # GET /api/calendar
│   │   └── metrics.py           # Prometheus exposition endpoint
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # App shell, routing, providers
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui base components
│   │   │   ├── panels/          # Dashboard panels
│   │   │   ├── charts/          # Chart wrappers
│   │   │   └── layout/          # Shell, sidebar, header
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts  # WS connection + auto-reconnect
│   │   │   └── useStore.ts      # Zustand stores per domain
│   │   ├── lib/
│   │   │   ├── types.ts         # TypeScript types matching backend models
│   │   │   └── utils.ts         # Formatters (bytes, duration, etc.)
│   │   └── styles/
│   │       └── globals.css      # Tailwind + glassmorphism custom utilities
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── LICENSE (MIT)
└── README.md
```

## Dashboard Layout

Single-page app with fixed icon sidebar and scrollable main content.

### Sidebar Navigation

Minimal icon sidebar: Overview (all panels), Downloads (expanded), Plex (expanded), Tdarr (expanded), Calendar (full view).

### Overview Page Panels

**1. Service Health Grid** — Responsive grid of glassmorphic cards (one per configured service). Each shows: service name, colored pulsing status dot, version, response time in ms. Click opens native UI.

**2. Active Downloads** — Stacked progress bars. Each item shows: name, speed, ETA, progress %, source service correlation (SABnzbd -> Sonarr/Radarr). Animated shimmer on active bars.

**3. Plex Streaming Activity** — Live session cards: username, media title, quality, direct play vs transcode, bandwidth per stream.

**4. Tdarr Transcode Pipeline** — Node status, active transcode with codec info and progress, queue depth, cumulative space savings.

**5. Upcoming Calendar** — Compact timeline of upcoming episodes/movies from Sonarr/Radarr calendars.

## Data Flow

### Collector Pipeline

```
Service APIs → Collectors (asyncio tasks) → WS Hub → Connected Clients
                                         → Prometheus metrics
```

### Collector Intervals

| Collector    | Interval | Services                    |
|-------------|----------|-----------------------------|
| health      | 30s      | All configured              |
| downloads   | 10s      | SABnzbd, Sonarr, Radarr     |
| streaming   | 15s      | Plex                        |
| transcoding | 30s      | Tdarr                       |
| calendar    | 5m       | Sonarr, Radarr              |

### WebSocket Protocol

Messages from server to client:

```json
{
  "type": "health" | "downloads" | "streaming" | "transcoding" | "calendar",
  "timestamp": "2026-02-19T18:30:00Z",
  "data": { ... }
}
```

Frontend stores: one Zustand store per domain. WS messages update the matching store, triggering targeted re-renders.

### REST Endpoints

Each domain has a GET endpoint for initial page load. Frontend fetches current state via REST on mount, then subscribes to WS for live updates.

### Prometheus Metrics

Exposed at `/metrics`:

- `mcc_service_up{service="..."}` — 1/0 per service
- `mcc_service_latency_seconds{service="..."}` — response time gauge
- `mcc_downloads_active` — current download count
- `mcc_downloads_speed_bytes` — total download speed
- `mcc_plex_streams_active` — active Plex sessions
- `mcc_plex_transcode_active` — active transcodes
- `mcc_tdarr_queue_size` — Tdarr pending queue
- `mcc_tdarr_space_saved_bytes` — cumulative savings

## Design System — Glassmorphism Cyberpunk

### Colors

| Token           | Value                           | Usage                    |
|----------------|---------------------------------|--------------------------|
| bg-base        | `#0a0a0f`                       | Page background          |
| surface        | `rgba(255,255,255,0.05)` + blur | Card backgrounds         |
| surface-hover  | `rgba(255,255,255,0.08)`        | Hover states             |
| border         | `rgba(255,255,255,0.10)`        | Card borders             |
| glow-primary   | `#00d4ff` (cyan)                | Active, primary          |
| glow-success   | `#00ff88` (neon green)          | Online, healthy          |
| glow-warning   | `#ffaa00` (amber)               | Degraded, slow           |
| glow-danger    | `#ff3366` (hot pink)            | Offline, errors          |
| glow-info      | `#7c5cfc` (purple)              | Informational            |
| text-primary   | `#e4e4e7`                       | Main text                |
| text-secondary | `#a1a1aa`                       | Supporting text          |
| text-muted     | `#71717a`                       | Disabled, tertiary       |

### Typography

- Body: Inter
- Numbers/stats/codes: JetBrains Mono

### Card Component

- `backdrop-filter: blur(16px)` + semi-transparent background
- 1px border with `rgba(255,255,255,0.10)`
- Status-colored inner glow
- `border-radius: 12px`
- Colored box-shadow glow when active

### Status Indicators

Pulsing dots with CSS animation and matching glow color.

### Progress Bars

Gradient fill (cyan to purple), animated shimmer on active, percentage overlay.

### Charts

Recharts with transparent backgrounds, glowing line strokes, subtle grid, animated transitions.

### Animations

- Cards: fade-in with stagger on load
- Status changes: brief pulse
- Progress bars: smooth width transitions
- Session cards: slide in/out on stream start/stop

## Configuration

Users provide service URLs and API keys via `.env`:

```env
# Services — only configured ones appear on dashboard
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your-key

RADARR_URL=http://localhost:7878
RADARR_API_KEY=your-key

# ... etc for each service

# Dashboard settings
MCC_PORT=8880
MCC_HOST=0.0.0.0
```

## Deployment

```bash
docker-compose up -d
```

Opens at `http://localhost:8880`. Optional Prometheus scrape at `http://localhost:8880/metrics`.
