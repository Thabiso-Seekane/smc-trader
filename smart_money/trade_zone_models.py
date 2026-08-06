"""Data models for the Trade Zone abstraction.

This module contains only data models (dataclasses) and holds no business
logic. A :class:`TradeZone` aggregates the outputs of Weeks 2-6 into a
single object the strategy layer can consume:

    * An :class:`OrderBlock` (Week 5).
    * One or more :class:`FairValueGap` (Week 6).
    * Nearby liquidity levels (Week 3).
    * Recent CHoCH / BOS structural events (Week 4).
    * Higher-timeframe alignment.

The aggregated zone is scored by the ConfluenceScorer producing a
0-100 :attr:`confluence_score` and a :attr:`confluence_level`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from smart_money.enums import ConfluenceLevel, OrderBlockType, TradeZoneStatus
from smart_money.fair_value_gap import FairValueGap
from smart_money.models import StructureEvent


@dataclass(slots=True)
class TradeZone:
    """A single high-probability trading zone.

    A TradeZone combines an Order Block, optional Fair Value Gaps, nearby
    liquidity, and recent structural events into one object. Downstream
    modules (e.g. the Week 7 Confluence Engine) evaluate TradeZone objects
    instead of merging unrelated structures on the fly.

    Attributes:
        direction: Bullish or bearish bias of the zone.
        high: Upper price of the zone (derived from the Order Block).
        low: Lower price of the zone (derived from the Order Block).
        origin_time: Timestamp of the originating Order Block.
        order_block: The Order Block that anchors this zone (may be None
            for zones built purely from FVGs / liquidity).
        fair_value_gaps: Fair Value Gaps that overlap this zone.
        liquidity_levels: Liquidity levels that interact with this zone.
        events: Structural events (CHoCH/BOS) that created / confirm this zone.
        timeframe: Label of the timeframe the zone was derived from.
        confluence_score: 0-100 aggregate score from the ConfluenceScorer.
        confluence_level: Quality tier derived from the confluence score.
        id: Unique identifier for the zone.
        active: Whether the zone is neither mitigated nor invalidated.
        mitigated: Whether price has returned into the zone.
        invalidated: Whether price closed beyond the far edge (destroyed).
    """

    direction: OrderBlockType
    high: float
    low: float
    origin_time: datetime
    order_block: object | None = None
    fair_value_gaps: list[FairValueGap] = field(default_factory=list)
    liquidity_levels: list[object] = field(default_factory=list)
    events: list[StructureEvent] = field(default_factory=list)
    timeframe: str = ""
    confluence_score: float = 0.0
    confluence_level: ConfluenceLevel = ConfluenceLevel.NONE
    id: UUID = field(default_factory=uuid4)
    active: bool = True
    mitigated: bool = False
    invalidated: bool = False

    # --- lifecycle helpers -----------------------------------
    @property
    def is_bullish(self) -> bool:
        """Return True when this is a bullish (buy-side) trade zone."""
        return self.direction == OrderBlockType.BULLISH

    @property
    def is_bearish(self) -> bool:
        """Return True when this is a bearish (sell-side) trade zone."""
        return self.direction == OrderBlockType.BEARISH

    @property
    def is_active(self) -> bool:
        """Return True when the zone is neither mitigated nor invalidated."""
        return not self.mitigated and not self.invalidated

    @property
    def status(self) -> TradeZoneStatus:
        """Return the lifecycle status of the zone."""
        if self.invalidated:
            return TradeZoneStatus.INVALIDATED
        if self.mitigated:
            return TradeZoneStatus.MITIGATED
        return TradeZoneStatus.ACTIVE

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
    def has_order_block(self) -> bool:
        """Return True when the zone is anchored by an Order Block."""
        return self.order_block is not None

    @property
    def has_fair_value_gap(self) -> bool:
        """Return True when the zone contains at least one FVG."""
        return len(self.fair_value_gaps) > 0

    @property
    def has_liquidity(self) -> bool:
        """Return True when the zone interacts with liquidity."""
        return len(self.liquidity_levels) > 0

    @property
    def event_count(self) -> int:
        """Return the number of structural events confirming this zone."""
        return len(self.events)

    def __hash__(self) -> int:
        """Hash by zone identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class TradeZoneMap:
    """Aggregated trade-zone analysis result.

    This is the output of :class:`smart_money.trade_zone_engine
    .TradeZoneEngine`. Future modules (Week 7 Confluence Engine, strategy)
    consume only this map and never need to know how the underlying
    structures were detected.

        * ``bullish``     — all bullish zones, ranked by confluence.
        * ``bearish``     — all bearish zones, ranked by confluence.
        * ``active``      — zones neither mitigated nor invalidated.
        * ``strongest``   — the highest-confluence active zone, if any.
        * ``all``         — full ranked list.
    """

    bullish: list[TradeZone] = field(default_factory=list)
    bearish: list[TradeZone] = field(default_factory=list)
    active: list[TradeZone] = field(default_factory=list)
    timeframe: str = ""

    @property
    def all(self) -> list[TradeZone]:
        """Return the full ranked list of zones."""
        return [*self.bullish, *self.bearish]

    @property
    def buy_side(self) -> list[TradeZone]:
        """Alias for :attr:`bullish` (query-style API)."""
        return self.bullish

    @property
    def sell_side(self) -> list[TradeZone]:
        """Alias for :attr:`bearish` (query-style API)."""
        return self.bearish

    @property
    def strongest(self) -> TradeZone | None:
        """Return the highest-confluence active zone, if any."""
        active = [z for z in self.active if not z.invalidated and z.is_active]
        if not active:
            return None
        return max(active, key=lambda z: z.confluence_score)

    @property
    def count(self) -> int:
        """Return the total number of zones."""
        return len(self.all)

    def __len__(self) -> int:
        return self.count


__all__ = ["TradeZone", "TradeZoneMap"]
