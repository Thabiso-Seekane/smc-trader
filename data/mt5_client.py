"""Thin MT5 integration wrapper.

This module is intentionally limited to communicating with MetaTrader 5.
It does not contain trading strategy or signal logic.
"""

from __future__ import annotations

from typing import Any

from config.settings import get_settings

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - depends on runtime environment
    mt5 = None

_connected = False


def _get_settings() -> Any:
    """Return the shared settings object."""

    return get_settings()


def _require_mt5() -> Any:
    """Raise a clear error if MetaTrader5 is unavailable."""

    if mt5 is None:
        raise RuntimeError("MetaTrader5 is not installed or could not be imported")
    return mt5


def _normalize_timeframe(timeframe: Any) -> Any:
    """Convert common string timeframes to their MetaTrader5 equivalents."""

    if isinstance(timeframe, str):
        mapping = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 60,
            "H4": 240,
            "D1": 1440,
            "W1": 10080,
        }
        return mapping.get(timeframe.upper(), timeframe)
    return timeframe


def connect() -> bool:
    """Initialize the MT5 terminal connection."""

    global _connected

    if _connected:
        return True

    settings = _get_settings()
    mt5_module = _require_mt5()

    initialized = mt5_module.initialize(
        login=settings.mt5_login,
        password=settings.mt5_password,
        server=settings.mt5_server,
    )
    if not initialized:
        raise RuntimeError(f"MT5 initialization failed: {mt5_module.last_error()}")

    _connected = True
    return True


def disconnect() -> None:
    """Shutdown the MT5 connection."""

    global _connected

    if not _connected:
        return

    mt5_module = _require_mt5()
    mt5_module.shutdown()
    _connected = False


def account_info() -> Any:
    """Return the current MT5 account information."""

    if not _connected:
        connect()

    mt5_module = _require_mt5()
    return mt5_module.account_info()


def terminal_info() -> Any:
    """Return the current MT5 terminal information."""

    if not _connected:
        connect()

    mt5_module = _require_mt5()
    return mt5_module.terminal_info()


def symbols() -> list[str]:
    """Return the list of available MT5 symbols."""

    if not _connected:
        connect()

    mt5_module = _require_mt5()
    return mt5_module.symbols_get()


def get_rates(symbol: str, timeframe: Any = None, count: int = 0) -> list[dict[str, Any]]:
    """Download OHLCV rates for the specified symbol."""

    if not _connected:
        connect()

    settings = _get_settings()
    mt5_module = _require_mt5()

    resolved_timeframe = _normalize_timeframe(timeframe or settings.default_timeframe)
    resolved_count = count or settings.candles_to_download

    return mt5_module.copy_rates_from_pos(
        symbol,
        resolved_timeframe,
        0,
        resolved_count,
    )


__all__ = ["connect", "disconnect", "account_info", "terminal_info", "symbols", "get_rates"]
