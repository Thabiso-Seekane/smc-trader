"""Equal-lows detection.

Groups proximate swing-low liquidity levels into clusters of equal lows.
When multiple swing lows exist close in price they form a stronger level
of sell-side liquidity.
"""

from __future__ import annotations

from dataclasses import dataclass

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityCluster, LiquidityLevel


@dataclass(slots=True)
class EqualLowDetector:
    """Detect equal-low clusters from a list of liquidity levels.

    Attributes:
        tolerance: Maximum price distance (as a fraction of price) between
            swing-low levels for them to be considered "equal".
            Default 0.0002 (0.02 %).
    """

    tolerance: float = 0.0002

    def detect(self, levels: list[LiquidityLevel]) -> list[LiquidityCluster]:
        """Group proximate swing-low levels into equal-low clusters.

        Args:
            levels: All detected liquidity levels (swing highs + lows).

        Returns:
            A list of :class:`LiquidityCluster` objects, one per group of
            proximate swing lows. Non-swing-low levels are ignored.
        """
        swing_lows = [l for l in levels if l.liquidity_type == LiquidityType.SWING_LOW]
        sorted_levels = sorted(swing_lows, key=lambda l: l.price)

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
                if (
                    abs(level.price - other.price) / max(level.price, 0.0001)
                    <= self.tolerance
                ):
                    group.append(other)
                    used.add(j)

            if len(group) >= 2:
                avg_price = sum(l.price for l in group) / len(group)
                clusters.append(
                    LiquidityCluster(
                        price=avg_price,
                        liquidity_type=LiquidityType.EQUAL_LOWS,
                        levels=group,
                        strength=len(group) * 1.0,
                    )
                )

        return clusters


__all__ = ["EqualLowDetector"]

