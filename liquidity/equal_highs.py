"""Equal-highs detection.

Groups proximate swing-high liquidity levels into clusters of equal highs.
When multiple swing highs exist close in price they form a stronger level
of buy-side liquidity that the market is more likely to target.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import pip_size
from liquidity.enums import LiquidityType
from liquidity.models import LiquidityCluster, LiquidityLevel


@dataclass(slots=True)
class EqualHighDetector:
    """Detect equal-high clusters from a list of liquidity levels.

    Attributes:
        tolerance: Maximum distance (in pips) between swing-high levels for
            them to be considered "equal". Default 2 (two pips).
        symbol: Instrument the levels belong to. Used to normalize the pip
            tolerance to an absolute price distance, since brokers differ
            in precision.
    """

    tolerance: float = 2
    symbol: str = ""

    def detect(self, levels: list[LiquidityLevel]) -> list[LiquidityCluster]:
        """Group proximate swing-high levels into equal-high clusters.

        Args:
            levels: All detected liquidity levels (swing highs + lows).

        Returns:
            A list of :class:`LiquidityCluster` objects, one per group of
            proximate swing highs. Non-swing-high levels are ignored.
        """
        max_gap = self.tolerance * pip_size(self.symbol)

        swing_highs = [
            l for l in levels if l.liquidity_type == LiquidityType.SWING_HIGH
        ]
        sorted_levels = sorted(swing_highs, key=lambda l: l.price)

        clusters: list[LiquidityCluster] = []
        used: set[int] = set()

        for i, level in enumerate(sorted_levels):
            if i in used:
                continue
            group: list[LiquidityLevel] = [level]
            used.add(i)
            for j, other in enumerate(sorted_levels):
                if j in used:
                    continue
                if abs(level.price - other.price) <= max_gap:
                    group.append(other)
                    used.add(j)

            if len(group) >= 2:
                avg_price = sum(l.price for l in group) / len(group)
                clusters.append(
                    LiquidityCluster(
                        price=avg_price,
                        liquidity_type=LiquidityType.EQUAL_HIGHS,
                        levels=group,
                        strength=len(group) * 1.0,
                    )
                )

        return clusters


__all__ = ["EqualHighDetector"]

