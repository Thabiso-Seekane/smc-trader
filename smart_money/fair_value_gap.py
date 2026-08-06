"""Fair Value Gap (FVG) — Week 6 skeleton.

This module defines the data model and a **placeholder** detector for Fair
Value Gaps. FVGs are gaps left between the wicks of three consecutive
candles when a strong displacement occurs:

    Bullish FVG:   low of candle[i+2] > high of candle[i]
    Bearish FVG:   high of candle[i+2] < low of candle[i]

The full detection algorithm is scheduled for Week 6. Until then the
detector returns an empty list so the :class:`TradeZone` abstraction is
already wired to consume FVGs without blocking the rest of the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

import pandas as pd

from smart_money.enums import OrderBlockType


@dataclass(slots=True)
class FairValueGap:
    """A single Fair Value Gap (imbalance) zone.

    Attributes:
        direction: Bullish or bearish bias of the gap.
        high: Upper price of the gap.
        low: Lower price of the gap.
        index: Candle index where the gap was detected (the middle candle).
        timestamp: Timestamp of the gap origin candle.
        strength: 0-100 imbalance strength (placeholder, default 0).
        id: Unique identifier for the gap.
        timeframe: Label of the timeframe the gap was derived from.
    """

    direction: OrderBlockType
    high: float
    low: float
    index: int
    timestamp: datetime
    strength: float = 0.0
    id: UUID = field(default_factory=uuid4)
    timeframe: str = ""

    @property
    def is_bullish(self) -> bool:
        """Return True when this is a bullish (buy-side) gap."""
        return self.direction == OrderBlockType.BULLISH

    @property
    def is_bearish(self) -> bool:
        """Return True when this is a bearish (sell-side) gap."""
        return self.direction == OrderBlockType.BEARISH

    @property
    def midpoint(self) -> float:
        """Return the midpoint price of the gap."""
        return (self.high + self.low) / 2.0

    @property
    def range(self) -> float:
        """Return the height of the gap."""
        return abs(self.high - self.low)


@dataclass(slots=True)
class FVGDetector:
    """Placeholder FVG detector.

    The full detection algorithm is implemented in Week 6. This stub pins
    the public API so downstream modules (TradeZone, ConfluenceScorer) can
    already reference it without breaking once the real algorithm lands.
    """

    lookback: int = 20

    def detect(
        self,
        candles: pd.DataFrame,
        timeframe: str = "",
    ) -> list[FairValueGap]:
        """Detect Fair Value Gaps.

        Currently a stub that returns an empty list. The real algorithm
        will be implemented in Week 6.

        Args:
            candles: OHLCV candle DataFrame.
            timeframe: Label attached to detected gaps.

        Returns:
            An empty list (placeholder).
        """
        del candles, timeframe
        return []


__all__ = ["FairValueGap", "FVGDetector"]
