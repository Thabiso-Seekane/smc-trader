"""Range liquidity detection.

This is Step 4 of the liquidity engine. A trading range forms when price
oscillates between a bounded upper and lower edge over a period of swing
history. The top of the range (``RANGE_HIGH``) is buy-side liquidity; the
bottom of the range (``RANGE_LOW``) is sell-side liquidity. Range edges
are classified as **external** liquidity because they represent major
structural levels at which price frequently reverses.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import pip_size
from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel
from structure.models import MarketStructure, Swing


@dataclass(slots=True)
class RangeDetector:
    """Detect consolidation ranges from the swing history.

    A range is recognized when the swing history alternates between
    highs and lows whose prices stay within a bounded band. The band's
    edges become the range-high (buy-side) and range-low (sell-side)
    liquidity levels.

    Attributes:
        lookback: Number of alternating swings required to confirm a
            range. Default 3 (three touch points per edge minimum).
        tolerance: Maximum height of the range (in pips). Ranges wider
            than this are treated as trends rather than consolidations.
            Default 20 (twenty pips).
        symbol: Instrument the swings belong to. Used to normalize the
            pip tolerance to an absolute price distance, since broker
            precision varies by symbol.
        timeframe: Label attached to generated range levels.
    """

    lookback: int = 3
    tolerance: float = 20
    symbol: str = ""
    timeframe: str = ""

    def detect(self, structure: MarketStructure) -> list[LiquidityLevel]:
        """Detect range-high and range-low liquidity levels.

        Args:
            structure: Market structure (swing history) from Week 2.

        Returns:
            A list containing at most one ``RANGE_HIGH`` level and one
            ``RANGE_LOW`` level, or an empty list when no confirmed range
            is found.
        """
        if structure is None or not structure.swings:
            return []

        swings = structure.swings
        if len(swings) < self.lookback * 2:
            return []

        highs = [s for s in swings if s.is_high]
        lows = [s for s in swings if not s.is_high]
        if not highs or not lows:
            return []

        range_high = max(highs, key=lambda s: s.price)
        range_low = min(lows, key=lambda s: s.price)

        max_height = self.tolerance * pip_size(self.symbol or "")
        height = range_high.price - range_low.price
        if height <= 0 or height > max_height:
            return []

        if not self._alternates(swings):
            return []

        levels: list[LiquidityLevel] = []
        if range_high is not None:
            levels.append(
                LiquidityLevel(
                    price=range_high.price,
                    liquidity_type=LiquidityType.RANGE_HIGH,
                    scope=LiquidityScope.EXTERNAL,
                    timeframe=self.timeframe,
                    swing_index=range_high.index,
                    timestamp=range_high.timestamp,
                    label=f"Range High @ {range_high.price:.5f}",
                )
            )
        if range_low is not None:
            levels.append(
                LiquidityLevel(
                    price=range_low.price,
                    liquidity_type=LiquidityType.RANGE_LOW,
                    scope=LiquidityScope.EXTERNAL,
                    timeframe=self.timeframe,
                    swing_index=range_low.index,
                    timestamp=range_low.timestamp,
                    label=f"Range Low @ {range_low.price:.5f}",
                )
            )
        return levels

    @staticmethod
    def _alternates(swings: list[Swing]) -> bool:
        """Return True when the swing sequence alternates high/low.

        A genuine consolidation range alternates between swing highs and
        swing lows. A run of consecutive highs or lows indicates a trend
        rather than a range.
        """
        for i in range(len(swings) - 1):
            if swings[i].is_high == swings[i + 1].is_high:
                return False
        return True


__all__ = ["RangeDetector"]
