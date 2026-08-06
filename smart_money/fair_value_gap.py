"""Fair Value Gap (FVG) — Week 6.

This module defines the :class:`FairValueGap` data model and the
:class:`FVGDetector` that locates three-candle imbalances. A Fair Value
Gap is a gap left between the wicks of three consecutive candles when a
strong displacement occurs:

    Bullish FVG:   low of candle[i+2] > high of candle[i]
    Bearish FVG:   high of candle[i+2] < low of candle[i]

Only displacement candles create FVGs. The detection pipeline gates each
candidate on the Week 4 displacement score, so poor-quality gaps are
removed immediately.

The model is backward-compatible with Week 5b — it keeps the
``is_bullish`` / ``is_bearish`` / ``midpoint`` / ``range`` properties that
the :class:`TradeZone` and :class:`ConfluenceScorer` rely on, while adding
rich fill / freshness / linking state for the Week 6 Imbalance Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

import numpy as np
import pandas as pd

from smart_money.displacement import DisplacementDetector, DisplacementScore
from smart_money.enums import (
    FillStatus,
    GapQuality,
    ImbalanceType,
    OrderBlockType,
)


@dataclass(slots=True)
class FairValueGap:
    """A single Fair Value Gap (imbalance) zone.

    Attributes:
        direction: Bullish or bearish bias of the gap.
        high: Upper price of the gap.
        low: Lower price of the gap.
        index: Candle index of the middle candle where the gap originated.
        origin_index: Candle index of the first candle of the 3-candle set.
        timestamp: Timestamp of the middle (origin) candle.
        created_at: When the gap object was created (UTC-naive).
        strength: 0-100 imbalance strength (set by the ranker).
        displacement: Full :class:`DisplacementScore` of the creating move.
        displacement_strength: 0-100 displacement shorthand.
        id: Unique identifier for the gap.
        timeframe: Label of the timeframe the gap was derived from.
        imbalance_type: Kind of imbalance (defaults to FAIR_VALUE_GAP).
        filled: True when price has fully traded through the gap.
        fill_percentage: 0-100 how much of the gap has been filled.
        fill_status: OPEN / PARTIAL / FILLED.
        touch_count: Number of candles that entered the gap.
        freshness: 0-100 freshness score (fresh=100, filled=0).
        linked_order_block: The Order Block aligned with this gap (optional).
        linked_structure_event: The structural event aligned with this gap.
        linked_liquidity: The liquidity level aligned with this gap.
        quality: Quality label derived from the strength score.
        invalidated: True when the gap is no longer usable.
    """

    direction: OrderBlockType
    high: float
    low: float
    index: int
    timestamp: datetime
    strength: float = 0.0
    id: UUID = field(default_factory=uuid4)
    timeframe: str = ""
    origin_index: int = -1
    created_at: datetime = field(
        default_factory=lambda: datetime.now()
    )
    imbalance_type: ImbalanceType = ImbalanceType.FAIR_VALUE_GAP
    displacement: DisplacementScore = field(default_factory=DisplacementScore)
    filled: bool = False
    fill_percentage: float = 0.0
    fill_status: FillStatus = FillStatus.OPEN
    touch_count: int = 0
    freshness: float = 100.0
    linked_order_block: object | None = None
    linked_structure_event: object | None = None
    linked_liquidity: object | None = None
    quality: GapQuality = GapQuality.NONE
    invalidated: bool = False

    # --- directional helpers -----------------------------------
    @property
    def is_bullish(self) -> bool:
        """Return True when this is a bullish (buy-side) gap."""
        return self.direction == OrderBlockType.BULLISH

    @property
    def is_bearish(self) -> bool:
        """Return True when this is a bearish (sell-side) gap."""
        return self.direction == OrderBlockType.BEARISH

    @property
    def displacement_strength(self) -> float:
        """Return the 0-100 displacement strength of the creating move."""
        return self.displacement.strength

    # --- geometry helpers --------------------------------------
    @property
    def midpoint(self) -> float:
        """Return the midpoint price of the gap."""
        return (self.high + self.low) / 2.0

    @property
    def range(self) -> float:
        """Return the height of the gap."""
        return abs(self.high - self.low)

    # --- lifecycle helpers -------------------------------------
    @property
    def is_active(self) -> bool:
        """Return True when the gap is open or only partially filled."""
        return not self.invalidated and not self.filled

    @property
    def is_partial(self) -> bool:
        """Return True when the gap is partially filled."""
        return self.fill_status == FillStatus.PARTIAL

    def __hash__(self) -> int:
        """Hash by gap identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class FVGDetector:
    """Detect Bullish and Bearish Fair Value Gaps.

    Detection pipeline:

        1. For each candle, check whether a 3-candle imbalance pattern
           exists (bullish ``low[i+2] > high[i]`` or bearish
           ``high[i+2] < low[i]``).
        2. Verify the middle candle has valid structural displacement.
        3. Reject gaps whose size is too small relative to the local ATR.

    Attributes:
        min_displacement: Minimum displacement strength (0-100) for a gap
            to be created.
        require_confirmed: When True, only candles with confirmed
            displacement create a gap.
        min_size_atr: Gap range must be at least this fraction of the local
            ATR to be kept.
        displacement: The :class:`DisplacementDetector` used to score the
            middle candle.
    """

    min_displacement: float = 30.0
    require_confirmed: bool = False
    min_size_atr: float = 0.2
    displacement: DisplacementDetector = field(default_factory=DisplacementDetector)

    def detect(
        self,
        candles: pd.DataFrame,
        timeframe: str = "",
    ) -> list[FairValueGap]:
        """Detect Fair Value Gaps in a candle frame.

        Args:
            candles: OHLCV candle DataFrame (``date``, ``open``, ``high``,
                ``low``, ``close``, ``volume``).
            timeframe: Label attached to detected gaps.

        Returns:
            A list of :class:`FairValueGap` objects, ordered by origin index.
        """
        if candles is None or candles.empty:
            return []
        if len(candles) < 3:
            return []

        gaps: list[FairValueGap] = []
        highs = candles["high"].to_numpy(dtype="float64")
        lows = candles["low"].to_numpy(dtype="float64")
        dates = candles["date"].to_numpy()

        for i in range(len(candles) - 2):
            gap = self._detect_at(candles, highs, lows, dates, i, timeframe)
            if gap is not None:
                gaps.append(gap)

        gaps.sort(key=lambda g: g.index)
        return gaps

    def _detect_at(
        self,
        candles: pd.DataFrame,
        highs: object,
        lows: object,
        dates: object,
        i: int,
        timeframe: str,
    ) -> FairValueGap | None:
        """Detect a single gap anchored at the middle candle ``i+1``."""
        # Bullish FVG: low[i+2] > high[i]
        if lows[i + 2] > highs[i] + 1e-12:
            direction = OrderBlockType.BULLISH
            g_high = float(lows[i + 2])
            g_low = float(highs[i])
        # Bearish FVG: high[i+2] < low[i]
        elif highs[i + 2] < lows[i] - 1e-12:
            direction = OrderBlockType.BEARISH
            g_high = float(lows[i])
            g_low = float(highs[i + 2])
        else:
            return None

        # Displacement gate on the middle candle.
        mid_index = i + 1
        displacement = self._score_displacement(candles, mid_index, direction)
        if displacement.strength < self.min_displacement:
            return None
        if self.require_confirmed and not displacement.confirmed:
            return None

        # Gap size gate (relative to ATR).
        if self._is_too_small(candles, mid_index, abs(g_high - g_low)):
            return None

        return FairValueGap(
            direction=direction,
            high=g_high,
            low=g_low,
            index=mid_index,
            origin_index=i,
            timestamp=pd.Timestamp(dates[mid_index]),
            timeframe=timeframe,
            displacement=displacement,
        )

    def _score_displacement(
        self,
        candles: pd.DataFrame,
        index: int,
        direction: OrderBlockType,
    ) -> DisplacementScore:
        """Score the displacement of the middle candle.

        A bullish gap is created by a bullish impulse candle; a bearish gap
        by a bearish impulse candle. The broken price is set to the candle's
        open so the displacement measures the candle's own thrust.
        """
        row = candles.iloc[index]
        broken_price = float(row["open"])
        is_bullish = direction == OrderBlockType.BULLISH
        return self.displacement.assess(
            candles, index, broken_price, is_bullish
        )

    def _is_too_small(
        self, candles: pd.DataFrame, index: int, size: float, atr_period: int = 14
    ) -> bool:
        """Return True when the gap range is a small fraction of ATR."""
        start = max(0, index - atr_period + 1)
        window = candles.iloc[start : index + 1]
        high = window["high"].to_numpy(dtype="float64")
        low = window["low"].to_numpy(dtype="float64")
        close = window["close"].to_numpy(dtype="float64")
        prev = np.roll(close, 1)
        prev[0] = close[0]
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
        atr = float(np.mean(tr)) if len(tr) else 0.0
        if atr <= 0:
            return False
        return size < self.min_size_atr * atr


__all__ = ["FairValueGap", "FVGDetector"]
