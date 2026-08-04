"""Liquidity ranking.

Computes a relative strength score for each liquidity level so the engine
can answer "which liquidity is strongest?" and "what is the next target?".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityLevel


@dataclass(slots=True)
class LiquidityRanker:
    """Ranks liquidity levels by importance.

    The strength score blends three signals:

        * Cluster multiplier: equal-high/low clusters are stronger than
          single swing levels.
        * Recency: more recent levels are more relevant.
        * Refinement: equal and range levels get a mild bonus because they
          represent a broader resting order book.

    Attributes:
        recency_window_days: Number of days considered "recent" for the
            recency bonus. Older levels are not penalised, only recent
            ones are boosted.
    """

    recency_window_days: int = 14

    def rank(self, levels: list[LiquidityLevel]) -> list[LiquidityLevel]:
        """Compute strength for each level and return them sorted.

        Args:
            levels: Liquidity levels to rank (may include swept levels).

        Returns:
            The same levels with :attr:`LiquidityLevel.strength` set,
            sorted by strength descending.
        """
        for level in levels:
            level.strength = self._score(level)

        return sorted(levels, key=lambda l: l.strength, reverse=True)

    def strongest(self, levels: list[LiquidityLevel]) -> LiquidityLevel | None:
        """Return the strongest level from the list.

        Args:
            levels: Liquidity levels to evaluate.

        Returns:
            The level with the highest strength, or ``None`` when empty.
        """
        if not levels:
            return None
        ranked = self.rank(levels)
        return ranked[0]

    def next_target(
        self,
        levels: list[LiquidityLevel],
        current_price: float,
    ) -> LiquidityLevel | None:
        """Identify the next likely liquidity target.

        The target is the nearest **active** (non-swept) level relative to
        the current price. This mirrors the behaviour of
        :class:`SweepDetector.next_target` so the engine consistently
        reports the closest resting liquidity pool as the next magnet.

        Args:
            levels: Liquidity levels to evaluate.
            current_price: The most recent close price.

        Returns:
            The nearest active level, or ``None`` when no active levels
            exist. Ties are broken toward the stronger level.
        """
        active = [l for l in levels if not l.swept]
        if not active:
            return None

        return min(
            active,
            key=lambda l: (abs(l.price - current_price), -self._score(l)),
        )

    def _score(self, level: LiquidityLevel) -> float:
        """Compute a normalized strength score for a single level."""
        score = 1.0

        # Cluster/equal levels are stronger than single swings.
        if level.liquidity_type in (LiquidityType.EQUAL_HIGHS, LiquidityType.EQUAL_LOWS):
            score += 2.0
        elif level.liquidity_type in (LiquidityType.RANGE_HIGH, LiquidityType.RANGE_LOW):
            score += 1.5
        elif level.liquidity_type in (LiquidityType.SWING_HIGH, LiquidityType.SWING_LOW):
            score += 1.0

        # Recency boost for levels created inside the window.
        if level.timestamp is not None:
            age_days = (datetime.utcnow() - level.timestamp).total_seconds() / 86400.0
            if 0 <= age_days <= self.recency_window_days:
                score += 0.5

        # Swept levels are less relevant going forward.
        if level.swept:
            score *= 0.2

        return round(score, 4)


__all__ = ["LiquidityRanker"]

