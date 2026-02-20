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
