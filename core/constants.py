"""Shared constants for the trading system."""

from __future__ import annotations

TIMEFRAMES = {
    "M1": "1 minute",
    "M5": "5 minutes",
    "M15": "15 minutes",
    "M30": "30 minutes",
    "H1": "1 hour",
    "H4": "4 hours",
    "D1": "1 day",
    "W1": "1 week",
}

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

SUPPORTED_SYMBOLS = ("XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD")

# Absolute price of a single "point" (smallest price increment) per symbol.
# Brokers differ in precision, so this must be normalized per symbol.
SYMBOL_POINT_SIZE = {
    "EURUSD": 0.00001,
    "GBPUSD": 0.00001,
    "AUDUSD": 0.00001,
    "USDJPY": 0.001,
    "XAUUSD": 0.001,
}

# Absolute price of a single "pip" per symbol. For 5-digit FX symbols one
# pip equals 10 points; for 3-digit JPY pairs one pip equals 1 point.
SYMBOL_PIP_SIZE = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "USDJPY": 0.01,
    "XAUUSD": 0.01,
}

# Fallbacks used when a symbol is unknown or empty.
_DEFAULT_POINT_SIZE = 0.00001
_DEFAULT_PIP_SIZE = 0.0001


def point_size(symbol: str) -> float:
    """Return the absolute price of one point for ``symbol``."""
    return SYMBOL_POINT_SIZE.get(symbol, _DEFAULT_POINT_SIZE)


def pip_size(symbol: str) -> float:
    """Return the absolute price of one pip for ``symbol``."""
    return SYMBOL_PIP_SIZE.get(symbol, _DEFAULT_PIP_SIZE)


__all__ = [
    "TIMEFRAMES",
    "DATE_FORMAT",
    "DATETIME_FORMAT",
    "SUPPORTED_SYMBOLS",
    "SYMBOL_POINT_SIZE",
    "SYMBOL_PIP_SIZE",
    "point_size",
    "pip_size",
]
