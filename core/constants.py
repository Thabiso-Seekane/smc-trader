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

__all__ = [
    "TIMEFRAMES",
    "DATE_FORMAT",
    "DATETIME_FORMAT",
    "SUPPORTED_SYMBOLS",
]
