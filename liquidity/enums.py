"""Enums for the liquidity engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class LiquidityType(str, Enum):
    """Classification of a liquidity pool."""

    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"
    EQUAL_HIGHS = "EQUAL_HIGHS"
    EQUAL_LOWS = "EQUAL_LOWS"
    RANGE_HIGH = "RANGE_HIGH"
    RANGE_LOW = "RANGE_LOW"
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class LiquidityStatus(str, Enum):
    """Lifecycle state of a liquidity pool."""

    ACTIVE = "ACTIVE"
    SWEPT = "SWEPT"
    TARGETED = "TARGETED"


__all__ = ["LiquidityType", "LiquidityStatus"]
