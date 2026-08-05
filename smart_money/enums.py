"""Enums for the Smart Money (CHoCH / BOS) engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class StructureEventType(str, Enum):
    """Type of structural event produced by the engine."""

    CHOCH = "CHOCH"
    BOS = "BOS"


class Direction(str, Enum):
    """Directional bias of a structural event."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class BreakSystem(str, Enum):
    """Whether a break of structure is internal or external.

    Internal breaks occur within the current dealing range (minor swing
    levels). External breaks occur at major structural levels (range
    extremes, weekly/day liquidity, major swing points).
    """

    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class DisplacementQuality(str, Enum):
    """Quality classification of a structural displacement."""

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


__all__ = [
    "StructureEventType",
    "Direction",
    "BreakSystem",
    "DisplacementQuality",
]
