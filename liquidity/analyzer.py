"""Liquidity analyzer — the public façade.

``LiquidityAnalyzer.analyze(df)`` wires together the Week 2 market
structure engine with the Week 3 liquidity detectors so callers interact
with a single entry point and receive a complete :class:`LiquidityMap`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from liquidity.detector import LiquidityDetector
from liquidity.enums import LiquidityScope
from liquidity.equal_highs import EqualHighDetector
from liquidity.equal_lows import EqualLowDetector
from liquidity.models import LiquidityLevel, LiquidityMap
from liquidity.range_detector import RangeDetector
from liquidity.ranking import LiquidityRanker
from liquidity.sweeps import SweepDetector
from structure.analyzer import MarketStructureAnalyzer


@dataclass(slots=True)
class LiquidityAnalyzer:
    """High-level orchestrator for liquidity analysis.

    Attributes:
        lookback: Fractal lookback forwarded to the Week 2 swing detector.
        tolerance: Equal high/low proximity tolerance (in pips).
        symbol: Instrument being analyzed. Used to normalize the pip
            tolerance to an absolute price distance, since broker precision
            varies by symbol.
        timeframe: Label attached to generated liquidity levels.
    """

    lookback: int = 2
    tolerance: float = 2
    symbol: str = ""
    timeframe: str = field(default="", kw_only=True)

    def analyze(self, df: pd.DataFrame) -> LiquidityMap:
        """Analyze a candle DataFrame and build the liquidity map.

        The pipeline is:

            1. Run Week 2 ``MarketStructureAnalyzer`` to get swings.
            2. Convert swings into buy/sell side liquidity levels.
            3. Cluster equal highs and equal lows.
            4. Detect range-high / range-low liquidity.
            5. Detect which levels have been swept.
            6. Rank levels by strength and choose the next target.

        Args:
            df: OHLCV candle DataFrame (``date``, ``open``, ``high``,
                ``low``, ``close``, ``volume``).

        Returns:
            A :class:`LiquidityMap` describing where liquidity sits,
            which pools are strongest, and what the next target is.
        """
        if df is None or df.empty:
            return LiquidityMap(timeframe=self.timeframe)

        structure = MarketStructureAnalyzer(lookback=self.lookback).analyze(df)
        detector = LiquidityDetector(timeframe=self.timeframe)
        ranker = LiquidityRanker()

        levels = detector.detect(structure)

        equal_highs = EqualHighDetector(
            tolerance=self.tolerance, symbol=self.symbol
        ).detect(levels)
        equal_lows = EqualLowDetector(
            tolerance=self.tolerance, symbol=self.symbol
        ).detect(levels)

        # Detect range-high / range-low liquidity from the swing history.
        range_levels = RangeDetector(
            tolerance=self.tolerance,
            symbol=self.symbol,
            timeframe=self.timeframe,
        ).detect(structure)

        # Augment the level list with clustered equal-high/low + range levels.
        augmented = list(levels)
        for cluster in [*equal_highs, *equal_lows]:
            augmented.append(
                LiquidityLevel(
                    price=cluster.price,
                    liquidity_type=cluster.liquidity_type,
                    scope=LiquidityScope.INTERNAL,
                    timeframe=self.timeframe,
                    label=f"{cluster.liquidity_type.value} @ {cluster.price:.5f}",
                )
            )
        augmented.extend(range_levels)

        # Determine sweeps using the full candle frame.
        SweepDetector().detect(augmented, df)

        # Rank and pick the strongest + next target.
        ranked = ranker.rank(augmented)
        strongest = ranked[0] if ranked else None
        current_price = float(df["close"].iloc[-1])
        next_target = ranker.next_target(augmented, current_price)

        return LiquidityMap(
            levels=augmented,
            clusters=[*equal_highs, *equal_lows],
            strongest=strongest,
            next_target=next_target,
            timeframe=self.timeframe,
        )


__all__ = ["LiquidityAnalyzer"]
