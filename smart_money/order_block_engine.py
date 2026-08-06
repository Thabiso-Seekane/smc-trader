"""Order Block Engine — the public façade for Week 5.

``OrderBlockEngine.analyze(df, structure, liquidity, events)`` wires
together Weeks 2-4 outputs (market structure, liquidity map, structural
events) with the Order Block detector, validator, mitigation detector, and
ranker so callers interact with a single entry point and receive a complete
:class:`OrderBlockMap`.

The engine also supports **multi-timeframe** analysis: pass a dict of
``{timeframe_label: DataFrame}`` to ``analyze_multi`` to rank zones across
multiple timeframes and return a merged map.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from smart_money.enums import OrderBlockType
from smart_money.mitigation import MitigationDetector
from smart_money.order_block_models import OrderBlock, OrderBlockMap
from smart_money.order_block_validator import OrderBlockValidator
from smart_money.order_blocks import OrderBlockDetector
from smart_money.ranking import OrderBlockRanker
from smart_money.validator import SmartMoneyValidator
from structure.models import MarketStructure


@dataclass(slots=True)
class OrderBlockEngine:
    """High-level orchestrator for Order Block detection.

    Attributes:
        lookback: Maximum candles walked back to find the origin candle.
        min_displacement: Minimum displacement strength (0-100) for a zone
            to be created.
        min_body_ratio: Minimum body-to-range ratio for the origin candle.
        require_confirmed: When True, only events with confirmed displacement
            seed an Order Block.
        timeframe: Label attached to detected zones.
    """

    lookback: int = 20
    min_displacement: float = 30.0
    min_body_ratio: float = 0.3
    require_confirmed: bool = False
    timeframe: str = field(default="", kw_only=True)

    def analyze(
        self,
        df: pd.DataFrame,
        structure: MarketStructure,
        liquidity,
        events,
    ) -> OrderBlockMap:
        """Detect, validate, mitigate, and rank Order Blocks.

        The pipeline is:

            1. Validate the candle, structure, and liquidity inputs.
            2. Detect candidate Order Blocks from structural events.
            3. Validate each zone (reject doji / tiny / weak).
            4. Detect mitigation, invalidation, and freshness.
            5. Rank zones and aggregate into an :class:`OrderBlockMap`.

        Args:
            df: OHLCV candle DataFrame.
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.
            events: Structural events (CHoCH/BOS) from the Week 4 engine.

        Returns:
            A :class:`OrderBlockMap` with bullish, bearish, active,
            mitigated, and invalidated zones.
        """
        SmartMoneyValidator().validate(df, structure, liquidity)

        detector = OrderBlockDetector(
            lookback=self.lookback,
            min_displacement=self.min_displacement,
            min_body_ratio=self.min_body_ratio,
            require_confirmed=self.require_confirmed,
        )
        validator = OrderBlockValidator(
            min_displacement=self.min_displacement,
            min_body_ratio=self.min_body_ratio,
        )
        mitigation = MitigationDetector()
        ranker = OrderBlockRanker()

        # 1) Detect candidate zones.
        candidates = detector.detect(
            events=_as_event_list(events),
            candles=df,
            timeframe=self.timeframe,
        )

        # 2) Validate.
        valid = [b for b in candidates if validator.is_valid(b, candles=df)]

        # 3) Mitigation / invalidation / freshness.
        mitigation.analyze(valid, candles=df)

        # 4) Rank.
        ranked = ranker.rank(valid, structure_events=_as_event_list(events), liquidity_map=liquidity)

        return self._build_map(ranked)

    def analyze_multi(
        self,
        frames: dict[str, pd.DataFrame],
        structures: dict[str, MarketStructure],
        liquidities: dict[str, object],
        events_by_tf: dict[str, object],
    ) -> OrderBlockMap:
        """Detect Order Blocks across multiple timeframes and merge them.

        Args:
            frames: Mapping of ``timeframe_label -> OHLCV DataFrame``.
            structures: Mapping of ``timeframe_label -> MarketStructure``.
            liquidities: Mapping of ``timeframe_label -> LiquidityMap``.
            events_by_tf: Mapping of ``timeframe_label -> events``.

        Returns:
            A merged :class:`OrderBlockMap` with all timeframe zones,
            ranked across the combined set.
        """
        all_blocks: list[OrderBlock] = []
        for tf, frame in frames.items():
            self.timeframe = tf
            mapped = self.analyze(
                df=frame,
                structure=structures.get(tf),
                liquidity=liquidities.get(tf),
                events=events_by_tf.get(tf, []),
            )
            all_blocks.extend(mapped.all)

        # Re-rank across all timeframes.
        ranker = OrderBlockRanker()
        ranked = ranker.rank(
            all_blocks,
            structure_events=[],
            liquidity_map=None,
        )
        return self._build_map(ranked)

    def _build_map(self, blocks: list[OrderBlock]) -> OrderBlockMap:
        """Aggregate ranked blocks into a map."""
        bullish = [b for b in blocks if b.direction == OrderBlockType.BULLISH]
        bearish = [b for b in blocks if b.direction == OrderBlockType.BEARISH]
        active = [b for b in blocks if b.is_active]
        mitigated = [b for b in blocks if b.mitigated and not b.invalidated]
        invalidated = [b for b in blocks if b.invalidated]
        return OrderBlockMap(
            bullish=bullish,
            bearish=bearish,
            active=active,
            mitigated=mitigated,
            invalidated=invalidated,
            timeframe=self.timeframe,
        )


def _as_event_list(events) -> list:
    """Normalize events (SmartMoneyAnalysis, EventHistory, or list) to a list."""
    if events is None:
        return []
    if isinstance(events, list):
        return events
    # SmartMoneyAnalysis / EventHistory expose .events or .history.
    for attr in ("events", "history"):
        if hasattr(events, attr):
            return list(getattr(events, attr))
    return []


__all__ = ["OrderBlockEngine"]
