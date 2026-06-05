"""
FlowCompiler Configuration Module.

Centralized configuration management using Pydantic Settings.
All environment variables are validated and typed at startup.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # ── OpenAI ───────────────────────────────────────────
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")
    openai_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for deterministic outputs",
    )

    # ── Database ─────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/flowcompiler",
        description="PostgreSQL connection string",
    )

    # ── Supabase (optional) ──────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""

    # ── Pipeline ─────────────────────────────────────────
    max_repair_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum repair loop iterations",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum retries per LLM call",
    )

    # ── Evaluation ───────────────────────────────────────
    max_concurrent_evaluations: int = Field(default=5, ge=1, le=20)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
