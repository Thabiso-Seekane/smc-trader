"""Swing liquidity detection.

This is Step 1 of the liquidity engine. The detector converts the Week 2
market structure into raw liquidity levels:

    * Every swing high  -> Buy Side Liquidity  (SWING_HIGH)
    * Every swing low   -> Sell Side Liquidity (SWING_LOW)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityLevel
from structure.models import MarketStructure, Swing


@dataclass(slots=True)
class LiquidityDetector:
    """Detects swing liquidity from a market structure.

    Attributes:
        timeframe: Label attached to generated levels (e.g. "M15").
    """

    timeframe: str = field(default="", kw_only=True)

    def detect(self, structure: MarketStructure) -> list[LiquidityLevel]:
        """Convert every swing into a liquidity level.

        Args:
            structure: Market structure from the Week 2 engine.

        Returns:
            A list of :class:`LiquidityLevel` objects. Swing highs become
            buy-side liquidity; swing lows become sell-side liquidity.
        """
        if structure is None:
            return []

        levels: list[LiquidityLevel] = []
        for swing in structure.swings:
            levels.append(self._from_swing(swing))
        return levels

    def _from_swing(self, swing: Swing) -> LiquidityLevel:
        """Create a liquidity level from a single swing point."""
        is_high = swing.is_high
        return LiquidityLevel(
            price=swing.price,
            liquidity_type=(
                LiquidityType.SWING_HIGH if is_high else LiquidityType.SWING_LOW
            ),
            timeframe=self.timeframe,
            swing_index=swing.index,
            timestamp=swing.timestamp,
            label=f"Swing {'High' if is_high else 'Low'} @ {swing.price:.5f}",
        )


__all__ = ["LiquidityDetector"]

