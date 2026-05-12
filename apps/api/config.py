"""
WaspNet Configuration Module
Centralized settings using pydantic-settings for validation.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "WaspNet"
    app_env: str = "development"
    app_debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://waspnet:waspnet_dev@localhost:5432/waspnet"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Dune SIM API (CORE) ---
    # SIM: Core data layer — all wallet data flows through this
    sim_api_key: str = ""
    sim_base_url: str = "https://api.sim.dune.com/v1"

    # --- JWT Auth ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""

    # --- Email (Resend) ---
    resend_api_key: str = ""
    resend_from_email: str = "alerts@waspnet.xyz"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()
