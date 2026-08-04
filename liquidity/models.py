"""Data models for the liquidity engine.

This module contains only data models (dataclasses) and holds no business
logic. Liquidity-level analysis is performed by the detector, equal highs/
lows, sweeps, and ranker modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from liquidity.enums import LiquidityStatus, LiquidityType


@dataclass(slots=True)
class LiquidityLevel:
    """A single liquidity pool (buy-side or sell-side).

    Attributes:
        price: The resting price of the pool.
        liquidity_type: Whether the pool sits above (buy-side) or below
            (sell-side) price, and its structural origin.
        strength: Relative measure of how significant this pool is.
            Computed by the ranker from swing score, clustering, recency.
        timeframe: The timeframe the level was derived from (e.g. "M15").
        created_at: When the level was created (UTC).
        swept: Whether price has already traded through this pool.
        id: Unique identifier for the level.
        swing_index: Index of the originating swing in the candle frame.
        timestamp: Timestamp of the originating swing/level.
        label: Optional human-readable label for visuals/debugging.
    """

    price: float
    liquidity_type: LiquidityType
    strength: float = 0.0
    timeframe: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    swept: bool = False
    id: UUID = field(default_factory=uuid4)
    swing_index: int | None = None
    timestamp: datetime | None = None
    label: str = ""

    @property
    def is_buy_side(self) -> bool:
        """Return True when this pool rests above price (sell stops)."""
        return self.liquidity_type in (
            LiquidityType.BUY_SIDE,
            LiquidityType.EQUAL_HIGHS,
            LiquidityType.RANGE_HIGH,
            LiquidityType.SWING_HIGH,
        )

    @property
    def is_sell_side(self) -> bool:
        """Return True when this pool rests below price (buy stops)."""
        return self.liquidity_type in (
            LiquidityType.SELL_SIDE,
            LiquidityType.EQUAL_LOWS,
            LiquidityType.RANGE_LOW,
            LiquidityType.SWING_LOW,
        )

    @property
    def status(self) -> LiquidityStatus:
        """Return the lifecycle state of the pool."""
        return LiquidityStatus.SWEPT if self.swept else LiquidityStatus.ACTIVE


@dataclass(slots=True)
class LiquidityCluster:
    """A cluster of liquidity levels that are close in price.

    Equal highs/lows are grouped into a single cluster so the engine can
    treat proximate pools as one larger, more significant pool.
    """

    price: float
    liquidity_type: LiquidityType
    levels: list[LiquidityLevel] = field(default_factory=list)
    strength: float = 0.0

    @property
    def size(self) -> int:
        """Return the number of levels in the cluster."""
        return len(self.levels)


@dataclass(slots=True)
class LiquidityMap:
    """The aggregated liquidity state for a given dataset.

    This is the output of the liquidity analyzer. It answers:

        * Where is buy-side liquidity?
        * Where is sell-side liquidity?
        * Which liquidity is strongest?
        * What is the next liquidity target?
        * Has liquidity already been swept?
    """

    levels: list[LiquidityLevel] = field(default_factory=list)
    clusters: list[LiquidityCluster] = field(default_factory=list)
    strongest: LiquidityLevel | None = None
    next_target: LiquidityLevel | None = None
    timeframe: str = ""

    @property
    def buy_side_levels(self) -> list[LiquidityLevel]:
        """Return all active buy-side liquidity levels."""
        return [level for level in self.levels if level.is_buy_side and not level.swept]

    @property
    def sell_side_levels(self) -> list[LiquidityLevel]:
        """Return all active sell-side liquidity levels."""
        return [level for level in self.levels if level.is_sell_side and not level.swept]

    @property
    def swept_levels(self) -> list[LiquidityLevel]:
        """Return all levels that have already been swept."""
        return [level for level in self.levels if level.swept]

    @property
    def active_levels(self) -> list[LiquidityLevel]:
        """Return all levels that have not yet been swept."""
        return [level for level in self.levels if not level.swept]

    def buy_side(self) -> list[LiquidityLevel]:
        """Alias for :attr:`buy_side_levels` (query-style API)."""
        return self.buy_side_levels

    def sell_side(self) -> list[LiquidityLevel]:
        """Alias for :attr:`sell_side_levels` (query-style API)."""
        return self.sell_side_levels


__all__ = ["LiquidityLevel", "LiquidityCluster", "LiquidityMap"]

