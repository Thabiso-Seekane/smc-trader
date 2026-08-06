"""Data models for the Order Block engine.

This module contains only data models (dataclasses) and holds no business
logic. Order-block detection, validation, mitigation, and ranking are
performed by the order_blocks, order_block_validator, mitigation, and
ranking modules respectively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from smart_money.enums import (
    Direction,
    FreshnessLevel,
    OrderBlockQuality,
    OrderBlockStatus,
    OrderBlockType,
)


@dataclass(slots=True)
class OrderBlock:
    """A single institutional order-block zone.

    This object represents one institutional buying or selling zone derived
    from a structural event (CHoCH/BOS) with valid displacement. It stores
    the full zone geometry and lifecycle state so downstream modules (and
    the strategy layer) never need to know how the zone was detected.

    Attributes:
        direction: Bullish (buy-side) or bearish (sell-side) bias.
        high: Upper price of the zone.
        low: Lower price of the zone.
        origin_index: Index of the origin candle in the source frame.
        origin_time: Timestamp of the origin candle.
        created_from_event: The structural event that produced this zone
            (CHoCH or BOS).
        displacement_score: 0-100 displacement strength of the creating
            event's break.
        id: Unique identifier for the zone.
        timeframe: Label of the timeframe the zone was derived from.
        fresh: Whether the zone is still fresh (not yet consumed).
        touch_count: Number of times price has entered the zone.
        mitigated: Whether price has returned into and consumed the zone.
        invalidated: Whether price closed beyond the far edge (destroyed).
        strength: 0-100 composite ranking score.
        quality: Quality label derived from the strength score.
    """

    direction: OrderBlockType
    high: float
    low: float
    origin_index: int
    origin_time: datetime
    created_from_event: Direction
    displacement_score: float = 0.0
    id: UUID = field(default_factory=uuid4)
    timeframe: str = ""
    fresh: bool = True
    touch_count: int = 0
    mitigated: bool = False
    invalidated: bool = False
    strength: float = 0.0
    quality: OrderBlockQuality = OrderBlockQuality.NONE

    # --- lifecycle helpers -----------------------------------
    @property
    def is_bullish(self) -> bool:
        """Return True when this is a bullish (buy-side) order block."""
        return self.direction == OrderBlockType.BULLISH

    @property
    def is_bearish(self) -> bool:
        """Return True when this is a bearish (sell-side) order block."""
        return self.direction == OrderBlockType.BEARISH

    @property
    def is_active(self) -> bool:
        """Return True when the zone is neither mitigated nor invalidated."""
        return not self.mitigated and not self.invalidated

    @property
    def status(self) -> OrderBlockStatus:
        """Return the lifecycle status of the zone."""
        if self.invalidated:
            return OrderBlockStatus.INVALIDATED
        if self.mitigated:
            return OrderBlockStatus.MITIGATED
        return OrderBlockStatus.ACTIVE

    # --- geometry helpers ------------------------------------
    @property
    def midpoint(self) -> float:
        """Return the midpoint price of the zone."""
        return (self.high + self.low) / 2.0

    @property
    def range(self) -> float:
        """Return the height of the zone."""
        return abs(self.high - self.low)

    @property
    def freshness(self) -> FreshnessLevel:
        """Return the freshness tier based on touch count / mitigation."""
        if self.mitigated or self.invalidated:
            return FreshnessLevel.MITIGATED
        if self.touch_count >= 2:
            return FreshnessLevel.TOUCHED_TWICE
        if self.touch_count == 1:
            return FreshnessLevel.TOUCHED_ONCE
        return FreshnessLevel.FRESH

    def __hash__(self) -> int:
        """Hash by zone identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class OrderBlockMap:
    """Aggregated order-block analysis result.

    This is the output of :class:`smart_money.order_block_engine
    .OrderBlockEngine`. Future modules consume only this map and never
    need to know how order blocks were detected.

        * ``bullish``     — all bullish (buy-side) zones, ranked.
        * ``bearish``     — all bearish (sell-side) zones, ranked.
        * ``active``      — zones neither mitigated nor invalidated.
        * ``mitigated``   — zones price has returned into and consumed.
        * ``invalidated`` — zones destroyed by a close beyond the far edge.
        * ``all``         — full ranked list.
    """

    bullish: list[OrderBlock] = field(default_factory=list)
    bearish: list[OrderBlock] = field(default_factory=list)
    active: list[OrderBlock] = field(default_factory=list)
    mitigated: list[OrderBlock] = field(default_factory=list)
    invalidated: list[OrderBlock] = field(default_factory=list)
    timeframe: str = ""

    @property
    def all(self) -> list[OrderBlock]:
        """Return the full chronological list of zones.

        Avoids duplicates by combining the directional lists.
        """
        return [*self.bullish, *self.bearish]

    @property
    def buy_side(self) -> list[OrderBlock]:
        """Alias for :attr:`bullish` (query-style API)."""
        return self.bullish

    @property
    def sell_side(self) -> list[OrderBlock]:
        """Alias for :attr:`bearish` (query-style API)."""
        return self.bearish

    @property
    def strongest(self) -> OrderBlock | None:
        """Return the highest-ranked active zone, if any."""
        active = [b for b in self.active if not b.invalidated]
        return max(active, key=lambda b: b.strength) if active else None

    @property
    def count(self) -> int:
        """Return the total number of zones."""
        return len(self.all)

    def __len__(self) -> int:
        return self.count


__all__ = ["OrderBlock", "OrderBlockMap"]
