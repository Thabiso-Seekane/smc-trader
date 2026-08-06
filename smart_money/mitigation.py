"""Mitigation, invalidation, and freshness detection for Order Blocks.

An Order Block is only fresh until price returns to it. This module tracks:

    * **Mitigation** — price has entered the zone and it has been consumed
      (touched). A mitigated zone is less reliable but not necessarily
      destroyed.
    * **Invalidation** — price has closed beyond the far edge of the zone,
      destroying it. The strategy must never use it again.
    * **Freshness** — a 0-100 freshness score based on how many times price
      has touched the zone.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from smart_money.enums import Direction
from smart_money.order_block_models import OrderBlock


@dataclass(slots=True)
class MitigationDetector:
    """Detect mitigation / invalidation / freshness for Order Blocks.

    Attributes:
        invalidate_on_close: When True, a zone is invalidated only when a
            candle *closes* beyond the far edge. When False, a mere wick
            beyond the far edge invalidates it.
    """

    invalidate_on_close: bool = True

    def analyze(
        self,
        blocks: list[OrderBlock],
        candles: pd.DataFrame,
    ) -> list[OrderBlock]:
        """Compute mitigation, invalidation, and touch count for each zone.

        Args:
            blocks: The Order Block zones to analyze.
            candles: OHLCV candle DataFrame.

        Returns:
            The same list of blocks, mutated with updated lifecycle state.
        """
        if not blocks or candles is None or candles.empty:
            return blocks

        closes = candles["close"].to_numpy(dtype="float64")
        highs = candles["high"].to_numpy(dtype="float64")
        lows = candles["low"].to_numpy(dtype="float64")

        for block in blocks:
            touches = self._count_touches(block, highs, lows, closes)
            block.touch_count = touches
            block.fresh = touches == 0

            invalidated = self._is_invalidated(block, highs, lows, closes)
            block.invalidated = invalidated

            # A zone is mitigated when it has been touched at least once and
            # has not been invalidated.
            block.mitigated = (not invalidated) and touches > 0

        return blocks

    def _count_touches(
        self,
        block: OrderBlock,
        highs: object,
        lows: object,
        closes: object,
    ) -> int:
        """Count the number of candles whose range enters the zone."""
        start = block.origin_index + 1
        if start >= len(highs):
            return 0
        count = 0
        for k in range(start, len(highs)):
            if highs[k] >= block.low and lows[k] <= block.high:
                count += 1
        return count

    def _is_invalidated(
        self,
        block: OrderBlock,
        highs: object,
        lows: object,
        closes: object,
    ) -> bool:
        """Return True when price has closed/wicked beyond the far edge."""
        start = block.origin_index + 1
        if start >= len(closes):
            return False
        if block.direction.value == Direction.BULLISH.value:
            # Bullish zone: invalidated when price closes below the low.
            for k in range(start, len(closes)):
                if self.invalidate_on_close:
                    if closes[k] < block.low:
                        return True
                else:
                    if lows[k] < block.low:
                        return True
        else:
            # Bearish zone: invalidated when price closes above the high.
            for k in range(start, len(closes)):
                if self.invalidate_on_close:
                    if closes[k] > block.high:
                        return True
                else:
                    if highs[k] > block.high:
                        return True
        return False


__all__ = ["MitigationDetector"]
