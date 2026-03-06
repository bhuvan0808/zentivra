"""Pydantic schemas for orchestrator configuration."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LLMAgentConfig(BaseModel):
    """Per-agent LLM provider and model selection."""

    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"

    model_config = {"extra": "allow"}


class LLMConfig(BaseModel):
    """Top-level LLM configuration with per-agent overrides."""

    default_provider: str = "groq"
    default_model: str = "llama-3.3-70b-versatile"
    agents: dict[str, LLMAgentConfig] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class CrawlConfig(BaseModel):
    max_pages_per_domain: int = Field(default=50, ge=1, le=500)
    request_timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_concurrent_urls: int = Field(default=5, ge=1, le=20)
    respect_robots_txt: bool = True

    model_config = {"extra": "allow"}


class ScheduleConfig(BaseModel):
    run_time: str = "06:00"
    timezone: str = "Asia/Kolkata"
    enabled: bool = True

    model_config = {"extra": "allow"}


class DeduplicationConfig(BaseModel):
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)

    model_config = {"extra": "allow"}


class RankingConfig(BaseModel):
    relevance_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    novelty_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    credibility_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    actionability_weight: float = Field(default=0.20, ge=0.0, le=1.0)

    model_config = {"extra": "allow"}


class DigestConfig(BaseModel):
    max_findings_per_section: int = Field(default=15, ge=1, le=100)
    include_appendix: bool = True

    model_config = {"extra": "allow"}


class NotificationsConfig(BaseModel):
    email_recipients: list[str] = Field(default_factory=list)
    send_on_empty: bool = False

    model_config = {"extra": "allow"}


class OrchestratorConfigSchema(BaseModel):
    """
    Full orchestrator configuration.

    Every section has defaults so the config works out-of-the-box.
    Extra keys at any level are preserved for custom user fields.
    """

    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    digest: DigestConfig = Field(default_factory=DigestConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)

    model_config = {"extra": "allow"}


class OrchestratorConfigResponse(BaseModel):
    """API response wrapping the config with metadata."""

    config: OrchestratorConfigSchema
    updated_at: Optional[datetime] = None
