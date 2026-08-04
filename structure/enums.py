"""Enums for the market structure engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class Trend(str, Enum):
    """Broad market trend state."""

    BULLISH = "Bullish"
    BEARISH = "Bearish"
    RANGE = "Range"
    TRANSITION = "Transition"


class SwingType(str, Enum):
    """Whether a swing is a high or a low."""

    HIGH = "High"
    LOW = "Low"


class StructureLabel(str, Enum):
    """Classification of a swing relative to the previous swing of the same type."""

    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low


__all__ = ["Trend", "SwingType", "StructureLabel"]
