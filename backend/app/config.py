"""
Zentivra Configuration Module.

Loads settings from .env file and YAML config files.
Uses pydantic-settings for validation and type safety.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DIGESTS_DIR = DATA_DIR / "digests"

# Ensure data directories exist
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
DIGESTS_DIR.mkdir(parents=True, exist_ok=True)


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./zentivra.db"
    database_echo: bool = False

    # ── LLM Providers ────────────────────────────────────────────────────
    llm_provider: Optional[str] = (
        None  # Optional explicit override: openrouter/groq/gemini/openai/anthropic
    )
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # LLM model overrides (per provider)
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    gemini_model: str = "gemini-2.0-flash-lite"
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ── Email ─────────────────────────────────────────────────────────────
    sendgrid_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 30
    email_from: str = "zentivra@localhost"
    email_recipients: str = ""  # Comma-separated list

    # ── Optional API Keys ─────────────────────────────────────────────────
    semantic_scholar_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None

    # ── Scheduling ────────────────────────────────────────────────────────
    digest_time: str = "06:00"
    timezone: str = "Asia/Kolkata"

    # ── CORS ──────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Auth / Redis ──────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    auth_token_ttl_hours: int = 2

    # ── App Settings ──────────────────────────────────────────────────────
    app_env: AppEnv = AppEnv.DEVELOPMENT
    log_level: str = "INFO"
    max_pages_per_domain: int = 50
    default_rate_limit_rpm: int = 10
    enable_semantic_dedup: bool = False
    max_urls_per_source: int = 3
    url_processing_timeout_seconds: int = 90
    source_processing_timeout_seconds: int = 300
    agent_timeout_seconds: int = 1200
    http_fetch_timeout_seconds: int = 20
    http_fetch_max_retries: int = 2
    llm_timeout_seconds: int = 45
    max_llm_rankings_per_run: int = 12
    stale_run_timeout_seconds: int = 1800

    @property
    def allowed_origin_list(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def email_recipient_list(self) -> list[str]:
        """Parse comma-separated email recipients into a list."""
        if not self.email_recipients:
            return []
        return [e.strip() for e in self.email_recipients.split(",") if e.strip()]

    @property
    def active_llm_provider(self) -> str:
        """Determine which LLM provider is configured."""
        configured = {
            "groq": bool(
                self.groq_api_key and self.groq_api_key != "your-groq-api-key-here"
            ),
            "openrouter": bool(
                self.openrouter_api_key
                and self.openrouter_api_key != "your-openrouter-api-key-here"
            ),
            "gemini": bool(
                self.gemini_api_key
                and self.gemini_api_key != "your-gemini-api-key-here"
            ),
            "openai": bool(
                self.openai_api_key
                and self.openai_api_key != "your-openai-api-key-here"
            ),
            "anthropic": bool(
                self.anthropic_api_key
                and self.anthropic_api_key != "your-anthropic-api-key-here"
            ),
        }

        if self.llm_provider:
            requested = self.llm_provider.strip().lower()
            if requested in configured and configured[requested]:
                return requested

        for provider in ("groq", "openrouter", "gemini", "openai", "anthropic"):
            if configured[provider]:
                return provider
        return "none"

    @property
    def has_email_configured(self) -> bool:
        """Check if any email delivery method is configured."""
        has_sendgrid = bool(
            self.sendgrid_api_key
            and self.sendgrid_api_key != "your-sendgrid-api-key-here"
        )
        has_smtp = bool(self.smtp_host)
        return has_sendgrid or has_smtp


# Singleton settings instance
settings = Settings()
