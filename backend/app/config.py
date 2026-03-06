"""
Zentivra Configuration Module.

Loads settings from .env file and YAML config files.
Uses pydantic-settings for validation and type safety.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DIGESTS_DIR = DATA_DIR / "digests"
LOGS_DIR = DATA_DIR / "logs"

# Ensure data directories exist
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
DIGESTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


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

    # ── LLM Providers ────────────────────────────────────────────────────
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # ── Email ─────────────────────────────────────────────────────────────
    sendgrid_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "zentivra@localhost"
    email_recipients: str = ""  # Comma-separated list

    # ── Optional API Keys ─────────────────────────────────────────────────
    semantic_scholar_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None

    # ── Scheduling ────────────────────────────────────────────────────────
    digest_time: str = "06:00"
    timezone: str = "Asia/Kolkata"

    # ── App Settings ──────────────────────────────────────────────────────
    app_env: AppEnv = AppEnv.DEVELOPMENT
    log_level: str = "INFO"
    max_pages_per_domain: int = 50
    default_rate_limit_rpm: int = 10

    @property
    def email_recipient_list(self) -> list[str]:
        """Parse comma-separated email recipients into a list."""
        if not self.email_recipients:
            return []
        return [e.strip() for e in self.email_recipients.split(",") if e.strip()]

    @property
    def active_llm_provider(self) -> str:
        """Determine which LLM provider is configured."""
        if self.groq_api_key and self.groq_api_key != "your-groq-api-key-here":
            return "groq"
        if (
            self.openrouter_api_key
            and self.openrouter_api_key != "your-openrouter-api-key-here"
        ):
            return "openrouter"
        if self.gemini_api_key and self.gemini_api_key != "your-gemini-api-key-here":
            return "gemini"
        if self.openai_api_key and self.openai_api_key != "your-openai-api-key-here":
            return "openai"
        if (
            self.anthropic_api_key
            and self.anthropic_api_key != "your-anthropic-api-key-here"
        ):
            return "anthropic"
        return "none"

    @property
    def has_email_configured(self) -> bool:
        """Check if any email delivery method is configured."""
        has_sendgrid = bool(
            self.sendgrid_api_key
            and self.sendgrid_api_key != "your-sendgrid-api-key-here"
        )
        has_smtp = bool(self.smtp_host and self.smtp_user)
        return has_sendgrid or has_smtp


# Singleton settings instance
settings = Settings()
