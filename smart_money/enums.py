"""Enums for the Smart Money (CHoCH / BOS) engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class StructureEventType(str, Enum):
    """Type of structural event produced by the engine."""

    CHOCH = "CHOCH"
    BOS = "BOS"
    MSS = "MSS"


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


class OrderBlockType(str, Enum):
    """Directional type of an Order Block zone."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class OrderBlockStatus(str, Enum):
    """Lifecycle state of an Order Block zone.

    * ``ACTIVE`` — fresh, not yet touched (or touched but still valid).
    * ``MITIGATED`` — price has returned into the zone and it has been
      consumed / partially used.
    * ``INVALIDATED`` — price closed beyond the far edge; the zone is
      destroyed and must never be used again.
    """

    ACTIVE = "ACTIVE"
    MITIGATED = "MITIGATED"
    INVALIDATED = "INVALIDATED"


class FreshnessLevel(str, Enum):
    """Freshness tier of an Order Block, used by the ranking.

    * ``FRESH`` — never touched (or barely touched).
    * ``TOUCHED_ONCE`` — price has entered the zone a single time.
    * ``TOUCHED_TWICE`` — price has entered the zone twice.
    * ``MITIGATED`` — the zone has already been consumed.
    """

    FRESH = "FRESH"
    TOUCHED_ONCE = "TOUCHED_ONCE"
    TOUCHED_TWICE = "TOUCHED_TWICE"
    MITIGATED = "MITIGATED"


class OrderBlockQuality(str, Enum):
    """Quality classification of an Order Block zone."""

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class ConfluenceLevel(str, Enum):
    """Strength of a Trade Zone's confluence.

    * ``NONE`` — no confluence (score 0).
    * ``WEAK`` — minimal confluence (1–39).
    * ``MODERATE`` — decent confluence (40–69).
    * ``STRONG`` — high-probability confluence (70+).
    """

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class TradeZoneStatus(str, Enum):
    """Lifecycle state of a Trade Zone.

    * ``ACTIVE`` — usable, not yet mitigated or invalidated.
    * ``MITIGATED`` — price has returned into the zone and consumed part of it.
    * ``INVALIDATED`` — price closed beyond the far edge; zone is destroyed.
    """

    ACTIVE = "ACTIVE"
    MITIGATED = "MITIGATED"
    INVALIDATED = "INVALIDATED"


__all__ = [
    "StructureEventType",
    "Direction",
    "BreakSystem",
    "DisplacementQuality",
    "OrderBlockType",
    "OrderBlockStatus",
    "FreshnessLevel",
    "OrderBlockQuality",
    "ConfluenceLevel",
    "TradeZoneStatus",
]
