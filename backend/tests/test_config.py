"""Tests for configuration loading."""

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
