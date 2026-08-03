"""Shared enums for the trading system."""

from __future__ import annotations

from enum import Enum


class Trend(str, Enum):
    """Broad market trend bias."""

    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"


class SwingType(str, Enum):
    """Type of swing structure."""

    HIGH = "high"
    LOW = "low"


class LiquidityType(str, Enum):
    """Type of liquidity pool."""

    SWING = "swing"
    INTERNAL = "internal"
    EXTERNAL = "external"


class Direction(str, Enum):
    """Directional bias for signal generation."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


__all__ = ["Trend", "SwingType", "LiquidityType", "Direction"]
