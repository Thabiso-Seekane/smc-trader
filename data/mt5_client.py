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
        mt5_module = _require_mt5()
        fallbacks = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 16385, "H4": 16388, "D1": 16408, "W1": 32769,
        }
        key = timeframe.upper()
        return getattr(mt5_module, f"TIMEFRAME_{key}", fallbacks.get(key, timeframe))
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


def resolve_symbol(symbol: str) -> str | None:
    """Resolve a portable symbol name to the connected broker's name.

    Brokers commonly expose gold as ``GOLD`` instead of ``XAUUSD`` or add
    suffixes such as ``EURUSD.a``. Exact matches are preferred, followed by
    well-known aliases and then prefix/suffix variants.
    """
    requested = str(symbol).strip()
    if not requested:
        return None
    available = [getattr(item, "name", item) for item in symbols()]
    names = [str(name) for name in available if name]
    by_upper = {name.upper(): name for name in names}
    key = requested.upper()
    if key in by_upper:
        return by_upper[key]

    aliases = {
        "XAUUSD": ("GOLD", "GOLD24-7"),
        "XAGUSD": ("SILVER",),
    }
    for alias in aliases.get(key, ()):
        if alias in by_upper:
            return by_upper[alias]

    variants = [
        name for name in names
        if name.upper().startswith(key) or name.upper().endswith(key)
    ]
    return min(variants, key=len) if variants else None


def symbol_info(symbol: str) -> Any:
    """Return read-only MT5 symbol metadata for market-data consumers."""
    if not _connected:
        connect()
    return _require_mt5().symbol_info(symbol)


def get_tick(symbol: str) -> Any:
    """Return the latest read-only bid/ask tick; never places an order."""
    if not _connected:
        connect()
    return _require_mt5().symbol_info_tick(symbol)


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


def order_calc_profit(action, symbol: str, volume: float, price_open: float, price_close: float):
    """Ask MT5 to calculate P&L in the connected account currency."""
    if not _connected:
        connect()
    return _require_mt5().order_calc_profit(action, symbol, volume, price_open, price_close)


def order_calc_margin(action, symbol: str, volume: float, price: float):
    """Ask MT5 to calculate required margin in account currency."""
    if not _connected:
        connect()
    return _require_mt5().order_calc_margin(action, symbol, volume, price)


def order_check(request: dict):
    """Run the broker/server preflight without sending an order."""
    if not _connected:
        connect()
    return _require_mt5().order_check(request)


def order_send(request: dict):
    """Send a preflighted request. Callers must enforce independent gates."""
    if not _connected:
        connect()
    return _require_mt5().order_send(request)


__all__ = ["connect", "disconnect", "account_info", "terminal_info", "symbols", "resolve_symbol", "symbol_info", "get_tick", "get_rates", "order_calc_profit", "order_calc_margin", "order_check", "order_send"]
