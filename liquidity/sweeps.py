"""Sweep detection for liquidity levels.

Determines whether a liquidity level has already been swept (price traded
through the level) and identifies which active level is the next likely
target based on current price proximity.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from liquidity.models import LiquidityLevel


@dataclass(slots=True)
class SweepDetector:
    """Detect whether liquidity levels have been swept by price.

    A buy-side level (resting above price) is swept when the candle
    high trades at or above the level's price. A sell-side level
    (resting below price) is swept when the candle low trades at or
    below the level's price.

    Attributes:
        lookahead: If True, sweeps are determined from the *entire*
            candle frame rather than only candles up to a given point.
    """

    lookahead: bool = True  # noqa: F841 - reserved for future refinement

    def detect(
        self,
        levels: list[LiquidityLevel],
        candles: pd.DataFrame,
    ) -> list[LiquidityLevel]:
        """Mark each level as swept or not based on price action.

        Args:
            levels: Liquidity levels to check.
            candles: OHLC DataFrame with ``high`` and ``low`` columns.

        Returns:
            The same list of levels with ``swept`` updated in place and
            returned. Swept levels have the ``SWEPT`` status; unswept
            levels remain ``ACTIVE``.
        """
        if not levels or candles is None or candles.empty:
            return levels

        highs = candles["high"].to_numpy()
        lows = candles["low"].to_numpy()
        max_high = float(highs.max())
        min_low = float(lows.min())

        for level in levels:
            if level.is_buy_side:
                level.swept = bool(max_high >= level.price)
            else:
                level.swept = bool(min_low <= level.price)

        return levels

    def next_target(
        self,
        levels: list[LiquidityLevel],
        current_price: float,
    ) -> LiquidityLevel | None:
        """Identify the nearest active liquidity level above or below price.

        Returns the **closest** active (non-swept) level regardless of
        buy/sell side.

        Args:
            levels: Liquidity levels to evaluate.
            current_price: The most recent close price.

        Returns:
            The closest active :class:`LiquidityLevel`, or ``None`` if
            no active levels remain.
        """
        active = [l for l in levels if not l.swept]
        if not active:
            return None

        def _distance(l: LiquidityLevel) -> float:
            return abs(l.price - current_price)

        return min(active, key=_distance)


__all__ = ["SweepDetector"]

