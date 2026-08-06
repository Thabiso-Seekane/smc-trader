"""Fill detection and freshness tracking for imbalance gaps.

Most FVG implementations only store ``filled=True / False``. This module
does better: it tracks a continuous **fill percentage** (0-100) by scanning
subsequent candles for how far price traded back into the gap, plus a
**freshness** score and a **touch count**.

Fill semantics:

    * A bullish gap (low..high) is filled as price trades down into it.
    * A bearish gap (low..high) is filled as price trades up into it.

Fill percentage is computed from the deepest excursion into the gap:
0% means price never entered; 100% means price reached the far edge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smart_money.enums import FillStatus, OrderBlockType
from smart_money.fair_value_gap import FairValueGap


@dataclass(slots=True)
class FillDetector:
    """Compute fill percentage, fill status, and freshness for gaps.

    Attributes:
        fill_smoothing: Optional smoothing on the fill percentage (0-1).
            When 0, the raw deepest-excursion percentage is used.
    """

    fill_smoothing: float = 0.0

    def analyze(
        self,
        gaps: list[FairValueGap],
        candles: pd.DataFrame,
    ) -> list[FairValueGap]:
        """Compute fill state and freshness for each gap.

        Args:
            gaps: The Fair Value Gap objects to analyze.
            candles: OHLCV candle DataFrame.

        Returns:
            The same list of gaps, mutated with ``fill_percentage``,
            ``fill_status``, ``filled``, ``touch_count``, and ``freshness``.
        """
        if not gaps or candles is None or candles.empty:
            return gaps

        highs = candles["high"].to_numpy(dtype="float64")
        lows = candles["low"].to_numpy(dtype="float64")

        for gap in gaps:
            pct, touches = self._measure(gap, highs, lows)
            gap.fill_percentage = round(pct, 2)
            gap.touch_count = touches
            gap.filled = pct >= 99.999
            gap.fill_status = self._status(pct)
            gap.freshness = self._freshness(pct, touches)

        return gaps

    def _measure(
        self,
        gap: FairValueGap,
        highs: object,
        lows: object,
    ) -> tuple[float, int]:
        """Measure the deepest fill percentage and touch count of a gap.

        Returns:
            A ``(fill_percentage, touch_count)`` tuple.
        """
        start = gap.index + 1
        if start >= len(highs):
            return 0.0, 0

        gap_low = gap.low
        gap_high = gap.high
        span = gap_high - gap_low
        if span <= 0:
            return 0.0, 0

        touches = 0
        deepest = 0.0
        for k in range(start, len(highs)):
            h = highs[k]
            l = lows[k]
            if h >= gap_low and l <= gap_high:
                touches += 1
            if gap.is_bullish:
                # Bullish gap: price fills by trading down into it.
                if l <= gap_high:
                    depth = max(0.0, gap_high - max(l, gap_low))
                    deepest = max(deepest, depth / span)
            else:
                # Bearish gap: price fills by trading up into it.
                if h >= gap_low:
                    depth = max(0.0, min(h, gap_high) - gap_low)
                    deepest = max(deepest, depth / span)

        pct = min(1.0, max(0.0, deepest)) * 100.0
        if self.fill_smoothing > 0 and gap.fill_percentage > 0:
            pct = (
                self.fill_smoothing * gap.fill_percentage
                + (1.0 - self.fill_smoothing) * pct
            )
        return pct, touches

    def _status(self, pct: float) -> FillStatus:
        """Map a fill percentage to a :class:`FillStatus`."""
        if pct >= 99.999:
            return FillStatus.FILLED
        if pct > 0.0:
            return FillStatus.PARTIAL
        return FillStatus.OPEN

    def _freshness(self, pct: float, touches: int) -> float:
        """Return a 0-100 freshness score.

        Brand new = 100, touched once = 70, multiple touches = 40,
        fully filled = 0.
        """
        if pct >= 99.999:
            return 0.0
        if touches == 0:
            return 100.0
        if touches == 1:
            return 70.0
        return 40.0


__all__ = ["FillDetector"]
