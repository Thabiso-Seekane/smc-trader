"""Application settings and configuration values."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment and .env."""

    # ----------------------------
    # MT5
    # ----------------------------
    mt5_login: int = Field(
        ..., validation_alias=AliasChoices("mt5_login", "MT5_LOGIN")
    )
    mt5_password: str = Field(
        ..., validation_alias=AliasChoices("mt5_password", "MT5_PASSWORD")
    )
    mt5_server: str = Field(
        ..., validation_alias=AliasChoices("mt5_server", "MT5_SERVER")
    )

    # ----------------------------
    # Trading
    # ----------------------------
    default_symbol: str = Field(
        "XAUUSD", validation_alias=AliasChoices("default_symbol", "DEFAULT_SYMBOL")
    )
    default_timeframe: str = Field(
        "M15", validation_alias=AliasChoices("default_timeframe", "DEFAULT_TIMEFRAME")
    )
    candles_to_download: int = Field(
        5000, validation_alias=AliasChoices("candles_to_download", "CANDLES_TO_DOWNLOAD")
    )
    risk_percent: float = Field(
        1.0, validation_alias=AliasChoices("risk_percent", "RISK_PERCENT")
    )

    # ----------------------------
    # Logging
    # ----------------------------
    log_level: str = Field(
        "INFO", validation_alias=AliasChoices("log_level", "LOG_LEVEL")
    )
    log_directory: str = Field(
        "logs", validation_alias=AliasChoices("log_directory", "LOG_DIRECTORY")
    )

    # ----------------------------
    # Data
    # ----------------------------
    data_directory: str = Field(
        "data_store", validation_alias=AliasChoices("data_directory", "DATA_DIRECTORY")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()

__all__ = [
    "Settings",
    "get_settings",
    "settings",
]