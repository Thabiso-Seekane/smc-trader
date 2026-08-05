"""Smart Money analyzer — the public façade.

``SmartMoneyAnalyzer.analyze(candles, structure, liquidity)`` wires together
the Week 2 market structure engine, the Week 3 liquidity engine, and the
Week 4 CHoCH / BOS detectors so callers interact with a single entry point
and receive a complete set of structural events.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from liquidity.models import LiquidityMap
from smart_money.bos import BosDetector
from smart_money.choch import ChoCHDetector
from smart_money.models import SmartMoneyAnalysis
from smart_money.validator import SmartMoneyValidator
from structure.models import MarketStructure


@dataclass(slots=True)
class SmartMoneyAnalyzer:
    """High-level orchestrator for CHoCH / BOS detection.

    Attributes:
        lookback: Fractal lookback forwarded to the structure engine.
        min_structure_points: Minimum structure points required before a
            CHoCH/BOS can fire.
        min_displacement: Minimum displacement strength (0–100) required
            for a structural break to be considered valid.
        pip_size: Absolute price of one pip, used to normalize the required
            displacement move.
        min_move_pips: Minimum move (in pips) beyond the broken level.
        timeframe: Label attached to the analysis result.
    """

    lookback: int = 2
    min_structure_points: int = 3
    min_displacement: float = 30.0
    pip_size: float = 0.0001
    min_move_pips: float = 1.0
    timeframe: str = field(default="", kw_only=True)

    def analyze(
        self,
        candles: pd.DataFrame,
        structure: MarketStructure,
        liquidity: LiquidityMap,
    ) -> SmartMoneyAnalysis:
        """Detect CHoCH and BOS structural events.

        The pipeline is:

            1. Validate the candle, structure, and liquidity inputs.
            2. Collect the swept sell-side and buy-side liquidity levels.
            3. Collect the external structural prices for BOS classification.
            4. Run the CHoCH detector.
            5. Run the BOS detector.
            6. Merge, de-duplicate, and sort events by confirmation index.

        Args:
            candles: OHLCV candle DataFrame (``date``, ``open``, ``high``,
                ``low``, ``close``, ``volume``).
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.

        Returns:
            A :class:`SmartMoneyAnalysis` containing the ordered list of
            structural events.
        """
        SmartMoneyValidator().validate(candles, structure, liquidity)

        choch = ChoCHDetector(
            min_structure_points=self.min_structure_points,
            min_displacement=self.min_displacement,
            pip_size=self.pip_size,
            min_move_pips=self.min_move_pips,
        )
        bos = BosDetector(
            min_structure_points=max(2, self.min_structure_points - 1),
            min_displacement=self.min_displacement,
            pip_size=self.pip_size,
            min_move_pips=self.min_move_pips,
        )

        events = choch.detect(
            structure=structure,
            candles=candles,
            swept_sell_side=liquidity.swept_levels,
            swept_buy_side=liquidity.swept_levels,
        )
        events.extend(
            bos.detect(
                structure=structure,
                candles=candles,
                external_prices=self._external_prices(liquidity),
            )
        )

        # De-duplicate and sort by confirmation index.
        unique: list = []
        seen: set[tuple] = set()
        for e in sorted(events, key=lambda e: e.confirmation_index):
            key = (e.event_type, e.direction, e.confirmation_index, e.broken_index)
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)

        return SmartMoneyAnalysis(events=unique, timeframe=self.timeframe)

    def _external_prices(self, liquidity: LiquidityMap) -> set[float]:
        """Return the set of external (major structural) level prices."""
        return {level.price for level in liquidity.external_levels}


__all__ = ["SmartMoneyAnalyzer"]
