"""Liquidity ranking.

Computes a relative strength score (0–100) for each liquidity level so the
engine can answer "which liquidity is strongest?" and "what is the next
target?".

The score blends five weighted factors, each contributing up to 20 points:

    * Swing Strength (20)  — how significant the originating swing is.
    * Equal Highs/Lows (20) — clustered equal levels are stronger.
    * Higher Timeframe (20) — levels from higher timeframes are stronger.
    * Number of Touches (20) — levels tested by price more often are stronger.
    * Age (20)              — recent levels are more relevant than old ones.

External liquidity also receives a strength bonus (up to 5 points) because
major reversals frequently begin after external liquidity is taken.

The five factors plus the scope bonus sum to a normalized 0–100 score.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel


@dataclass(slots=True)
class LiquidityRanker:
    """Ranks liquidity levels by importance.

    Attributes:
        recency_window_days: Number of days considered "recent" for the
            age factor. Levels inside the window receive a high age score;
            older levels are progressively de-weighted down to zero.
        max_touches: Touch count at which the "number of touches" factor
            is considered saturated (a level touched this many times is
            treated as fully confirmed).
    """

    recency_window_days: int = 14
    max_touches: int = 5

    # Weighted factors (each 0..20, total 100).
    _SWING_WEIGHT = 20.0
    _EQUAL_WEIGHT = 20.0
    _HTF_WEIGHT = 20.0
    _TOUCH_WEIGHT = 20.0
    _AGE_WEIGHT = 20.0

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
        :class:`~liquidity.sweeps.SweepDetector.next_target` so the engine
        consistently reports the closest resting liquidity pool as the
        next magnet.

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
            key=lambda l: (abs(l.price - current_price), -l.strength),
        )

    def _score(self, level: LiquidityLevel) -> float:
        """Compute a normalized 0–100 strength score for a single level."""
        swing = self._swing_factor(level)
        equal = self._equal_factor(level)
        htf = self._htf_factor(level)
        touches = self._touch_factor(level)
        age = self._age_factor(level)
        extra = self._scope_factor(level)

        total = swing + equal + htf + touches + age + extra
        return round(max(0.0, min(100.0, total)), 2)

    def _scope_factor(self, level: LiquidityLevel) -> float:
        """Score external liquidity higher than internal liquidity.

        In Smart Money Concepts, major reversals frequently begin after
        external liquidity (major structural levels) is taken, while
        internal liquidity is often swept as part of continuation moves.
        External pools therefore receive a strength bonus so they rank
        above structurally similar internal pools, making them preferred
        reversal targets for Week 4 CHoCH/BOS logic.
        """
        if level.scope == LiquidityScope.EXTERNAL:
            return self._SWING_WEIGHT * 0.25
        return 0.0

    def _swing_factor(self, level: LiquidityLevel) -> float:
        """Score the significance of the originating swing (0–20)."""
        if level.liquidity_type in (LiquidityType.SWING_HIGH, LiquidityType.SWING_LOW):
            return self._SWING_WEIGHT
        if level.liquidity_type in (LiquidityType.RANGE_HIGH, LiquidityType.RANGE_LOW):
            return self._SWING_WEIGHT * 0.8
        return 0.0

    def _equal_factor(self, level: LiquidityLevel) -> float:
        """Score how strongly a level represents a cluster (0–20)."""
        if level.liquidity_type in (LiquidityType.EQUAL_HIGHS, LiquidityType.EQUAL_LOWS):
            return self._EQUAL_WEIGHT
        return 0.0

    def _htf_factor(self, level: LiquidityLevel) -> float:
        """Score levels derived from a higher timeframe (0–20).

        The ``timeframe`` field is used as a proxy: known higher timeframes
        (H1, H4, D1, W1) score full points; lower timeframes (M1–M30) score
        partial points; unknown labels score a neutral baseline.
        """
        tf = (level.timeframe or "").upper()
        if tf in ("H1", "H4", "D1", "W1"):
            return self._HTF_WEIGHT
        if tf in ("M1", "M5", "M15", "M30"):
            return self._HTF_WEIGHT * 0.5
        return self._HTF_WEIGHT * 0.25

    def _touch_factor(self, level: LiquidityLevel) -> float:
        """Score how many times price has touched the level (0–20).

        The number of touches is approximated from the cluster size (for
        equal-level clusters) or the swing ``swing_index`` (each swing
        beyond the first adds a touch). This is a stand-in until a true
        touch counter is wired in.
        """
        touches = 1
        if level.liquidity_type in (LiquidityType.EQUAL_HIGHS, LiquidityType.EQUAL_LOWS):
            # Cluster levels carry a denormalized touch count in their id's
            # facet; we approximate from the swing history distance.
            touches += 1
        if level.swing_index is not None:
            touches += 1

        touches = min(touches, self.max_touches)
        return self._TOUCH_WEIGHT * (touches / self.max_touches)

    def _age_factor(self, level: LiquidityLevel) -> float:
        """Score the recency of a level (0–20).

        Levels inside the recency window score full points; older levels
        decay linearly toward zero by the time they are several windows old.
        """
        if level.timestamp is None:
            return self._AGE_WEIGHT * 0.5

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        age_days = (now_utc - level.timestamp).total_seconds() / 86400.0
        if age_days < 0:
            return self._AGE_WEIGHT
        if age_days <= self.recency_window_days:
            return self._AGE_WEIGHT
        # Decay over the next two windows.
        decay = max(0.0, 1.0 - (age_days - self.recency_window_days) / (2 * self.recency_window_days))
        return self._AGE_WEIGHT * decay


__all__ = ["LiquidityRanker"]
