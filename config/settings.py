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
    minimum_confluence: float = Field(
        70.0, validation_alias=AliasChoices("minimum_confluence", "MINIMUM_CONFLUENCE")
    )
    minimum_risk_reward: float = Field(
        2.0, validation_alias=AliasChoices("minimum_risk_reward", "MINIMUM_RISK_REWARD")
    )
    minimum_displacement: float = Field(
        0.0, validation_alias=AliasChoices("minimum_displacement", "MINIMUM_DISPLACEMENT")
    )
    require_liquidity_sweep: bool = Field(
        False, validation_alias=AliasChoices("require_liquidity_sweep", "REQUIRE_LIQUIDITY_SWEEP")
    )
    premium_discount_match: bool = Field(
        False, validation_alias=AliasChoices("premium_discount_match", "PREMIUM_DISCOUNT_MATCH")
    )

    # ----------------------------
    # Week 11 paper execution safety
    # ----------------------------
    trading_mode: str = Field(
        "paper", validation_alias=AliasChoices("trading_mode", "TRADING_MODE")
    )
    live_trading_enabled: bool = Field(
        False, validation_alias=AliasChoices("live_trading_enabled", "LIVE_TRADING_ENABLED")
    )
    paper_initial_balance: float = Field(
        10_000.0, validation_alias=AliasChoices("paper_initial_balance", "PAPER_INITIAL_BALANCE")
    )
    paper_database: str = Field(
        "data_store/paper_trading.db", validation_alias=AliasChoices("paper_database", "PAPER_DATABASE")
    )
    execution_strategy_id: str = Field(
        "smc_v1", validation_alias=AliasChoices("execution_strategy_id", "EXECUTION_STRATEGY_ID")
    )
    execution_magic_number: int = Field(
        501001, validation_alias=AliasChoices("execution_magic_number", "EXECUTION_MAGIC_NUMBER")
    )
    max_open_trades: int = Field(
        3, validation_alias=AliasChoices("max_open_trades", "MAX_OPEN_TRADES")
    )
    maximum_daily_loss_percent: float = Field(
        3.0, validation_alias=AliasChoices("maximum_daily_loss_percent", "MAXIMUM_DAILY_LOSS_PERCENT")
    )
    max_spread_points: float = Field(
        30.0, validation_alias=AliasChoices("max_spread_points", "MAX_SPREAD_POINTS")
    )
    live_risk_acknowledgement: str = Field(
        "", validation_alias=AliasChoices("live_risk_acknowledgement", "LIVE_RISK_ACKNOWLEDGEMENT")
    )
    live_max_margin_fraction: float = Field(
        0.25, validation_alias=AliasChoices("live_max_margin_fraction", "LIVE_MAX_MARGIN_FRACTION")
    )
    live_max_deviation_points: int = Field(
        20, validation_alias=AliasChoices("live_max_deviation_points", "LIVE_MAX_DEVIATION_POINTS")
    )
    live_order_comment: str = Field(
        "smc_trader", validation_alias=AliasChoices("live_order_comment", "LIVE_ORDER_COMMENT")
    )

    @property
    def live_trading_authorized(self) -> bool:
        """Return True only when live mode and the live env gate are both enabled."""

        return self.trading_mode.lower() == "live" and self.live_trading_enabled

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
