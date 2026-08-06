"""Imbalance Engine — the public façade for Week 6.

``ImbalanceEngine.analyze(df, structure, liquidity, events, order_blocks)``
wires together the Fair Value Gap detector, validator, fill detector, link
builder, and ranker so callers interact with a single entry point and
receive a complete :class:`ImbalanceMap`.

The engine is designed around the idea that a **Fair Value Gap is just one
type of imbalance**. Future imbalance types (Volume Imbalance, Opening Gap,
Liquidity Void, Inefficient Move) can be added by registering new detectors
without redesigning the pipeline. Week 7 simply consumes the
:class:`ImbalanceMap` and never needs to know how an FVG was found.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from smart_money.enums import FillStatus, OrderBlockType
from smart_money.fair_value_gap import FVGDetector, FairValueGap
from smart_money.fills import FillDetector
from smart_money.imbalance_ranking import ImbalanceRanker
from smart_money.imbalance_validator import ImbalanceValidator
from smart_money.validator import SmartMoneyValidator
from structure.models import MarketStructure


@dataclass(slots=True)
class ImbalanceMap:
    """Aggregated imbalance-gap analysis result.

    This is the output of :class:`ImbalanceEngine`. Future modules consume
    only this map and never need to know how gaps were detected.

        * ``bullish``  — all bullish (buy-side) gaps, ranked.
        * ``bearish``  — all bearish (sell-side) gaps, ranked.
        * ``active``   — gaps neither fully filled nor invalidated.
        * ``partial``  — gaps that are partially filled.
        * ``filled``   — gaps that have been fully traded through.
        * ``all``      — full ranked list.
    """

    bullish: list[FairValueGap] = field(default_factory=list)
    bearish: list[FairValueGap] = field(default_factory=list)
    active: list[FairValueGap] = field(default_factory=list)
    partial: list[FairValueGap] = field(default_factory=list)
    filled: list[FairValueGap] = field(default_factory=list)
    timeframe: str = ""

    @property
    def all(self) -> list[FairValueGap]:
        """Return the full ranked list of gaps."""
        return [*self.bullish, *self.bearish]

    @property
    def buy_side(self) -> list[FairValueGap]:
        """Alias for :attr:`bullish` (query-style API)."""
        return self.bullish

    @property
    def sell_side(self) -> list[FairValueGap]:
        """Alias for :attr:`bearish` (query-style API)."""
        return self.bearish

    @property
    def strongest(self) -> FairValueGap | None:
        """Return the highest-strength active gap, if any."""
        active = [g for g in self.active if not g.invalidated]
        return max(active, key=lambda g: g.strength) if active else None

    @property
    def count(self) -> int:
        """Return the total number of gaps."""
        return len(self.all)

    def __len__(self) -> int:
        return self.count


@dataclass(slots=True)
class ImbalanceEngine:
    """High-level orchestrator for imbalance (FVG) detection.

    Attributes:
        timeframe: Label attached to detected gaps.
        min_displacement: Minimum displacement strength (0-100) for a gap
            to be created.
        require_confirmed: When True, only confirmed displacement creates a
            gap.
        min_size_atr: Minimum gap size as a fraction of local ATR.
        reject_in_range: When True, reject gaps created inside a choppy
            range.
    """

    timeframe: str = field(default="", kw_only=True)
    min_displacement: float = 30.0
    require_confirmed: bool = False
    min_size_atr: float = 0.2
    reject_in_range: bool = False

    def analyze(
        self,
        df: pd.DataFrame,
        structure: MarketStructure,
        liquidity,
        events,
        order_blocks=None,
    ) -> ImbalanceMap:
        """Detect, validate, fill, link, and rank imbalance gaps.

        The pipeline is:

            1. Validate the candle, structure, and liquidity inputs.
            2. Detect candidate Fair Value Gaps from displacement + the
               3-candle pattern.
            3. Validate each gap (reject tiny / no-displacement / filled).
            4. Detect fill percentage, status, and freshness.
            5. Link each gap to aligned Order Blocks, structural events,
               and liquidity.
            6. Rank gaps and aggregate into an :class:`ImbalanceMap`.

        Args:
            df: OHLCV candle DataFrame.
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.
            events: Structural events (CHoCH/BOS) from the Week 4 engine.
            order_blocks: Order Block map from the Week 5 engine.

        Returns:
            An :class:`ImbalanceMap` with bullish, bearish, active, partial,
            and filled gaps.
        """
        SmartMoneyValidator().validate(df, structure, liquidity)

        detector = FVGDetector(
            min_displacement=self.min_displacement,
            require_confirmed=self.require_confirmed,
            min_size_atr=self.min_size_atr,
        )
        validator = ImbalanceValidator(
            min_displacement=self.min_displacement,
            min_size_atr=self.min_size_atr,
            reject_in_range=self.reject_in_range,
        )
        fills = FillDetector()
        ranker = ImbalanceRanker()

        # 1) Detect candidate gaps.
        candidates = detector.detect(df, timeframe=self.timeframe)

        # 2) Validate.
        valid = [g for g in candidates if validator.is_valid(g, candles=df)]

        # 3) Fill / freshness.
        fills.analyze(valid, candles=df)

        # 4) Link to OB / events / liquidity.
        self._link(valid, order_blocks, liquidity, events)

        # 5) Rank.
        ranked = ranker.rank(
            valid,
            structure_events=_as_event_list(events),
            liquidity_map=liquidity,
        )

        return self._build_map(ranked)

    def analyze_multi(
        self,
        frames: dict[str, pd.DataFrame],
        structures: dict[str, MarketStructure],
        liquidities: dict[str, object],
        events_by_tf: dict[str, object],
        order_blocks_by_tf: dict[str, object] | None = None,
    ) -> ImbalanceMap:
        """Detect imbalance gaps across multiple timeframes and merge them.

        Args:
            frames: Mapping of ``timeframe_label -> OHLCV DataFrame``.
            structures: Mapping of ``timeframe_label -> MarketStructure``.
            liquidities: Mapping of ``timeframe_label -> LiquidityMap``.
            events_by_tf: Mapping of ``timeframe_label -> events``.
            order_blocks_by_tf: Mapping of ``timeframe_label -> OrderBlockMap``.

        Returns:
            A merged :class:`ImbalanceMap` with all timeframe gaps, ranked
            across the combined set.
        """
        all_gaps: list[FairValueGap] = []
        for tf, frame in frames.items():
            self.timeframe = tf
            mapped = self.analyze(
                df=frame,
                structure=structures.get(tf),
                liquidity=liquidities.get(tf),
                events=events_by_tf.get(tf, []),
                order_blocks=(order_blocks_by_tf or {}).get(tf),
            )
            all_gaps.extend(mapped.all)

        ranker = ImbalanceRanker()
        ranked = ranker.rank(all_gaps)
        return self._build_map(ranked)

    def _link(self, gaps, order_blocks, liquidity, events=None) -> None:
        """Link each gap to aligned Order Blocks, events, and liquidity."""
        blocks = _as_block_list(order_blocks)
        levels = _as_level_list(liquidity)
        event_list = _as_event_list(events)

        for gap in gaps:
            gap.linked_order_block = self._find_aligned_block(gap, blocks)
            gap.linked_liquidity = self._find_aligned_level(gap, levels)
            gap.linked_structure_event = self._find_aligned_event(gap, event_list)

    def _find_aligned_block(self, gap: FairValueGap, blocks) -> object | None:
        """Find the Order Block aligned with this gap (direction + overlap)."""
        for block in blocks:
            if getattr(block, "direction", None) != gap.direction:
                continue
            if _overlaps(gap.low, gap.high, block):
                return block
        return None

    def _find_aligned_level(self, gap: FairValueGap, levels) -> object | None:
        """Find the liquidity level aligned with this gap."""
        for level in levels:
            price = getattr(level, "price", None)
            if price is None:
                continue
            if gap.low <= float(price) <= gap.high:
                return level
        return None

    def _find_aligned_event(self, gap: FairValueGap, events) -> object | None:
        """Find the structural event (CHoCH/BOS) aligned with this gap.

        An event is aligned when it shares the gap's direction and its
        confirmation index is at or before the gap's origin.
        """
        for event in events:
            is_bullish = getattr(event, "is_bullish", None)
            if is_bullish is None:
                continue
            event_is_bullish = bool(is_bullish)
            gap_is_bullish = gap.direction == OrderBlockType.BULLISH
            if event_is_bullish != gap_is_bullish:
                continue
            index = getattr(event, "confirmation_index", None)
            if index is not None and index > gap.index:
                continue
            return event
        return None

    def _build_map(self, gaps: list[FairValueGap]) -> ImbalanceMap:
        """Aggregate ranked gaps into a map."""
        bullish = [g for g in gaps if g.direction == OrderBlockType.BULLISH]
        bearish = [g for g in gaps if g.direction == OrderBlockType.BEARISH]
        active = [g for g in gaps if g.is_active]
        partial = [g for g in gaps if g.is_partial]
        filled = [g for g in gaps if g.fill_status == FillStatus.FILLED]
        return ImbalanceMap(
            bullish=bullish,
            bearish=bearish,
            active=active,
            partial=partial,
            filled=filled,
            timeframe=self.timeframe,
        )


def _as_event_list(events) -> list:
    """Normalize events (SmartMoneyAnalysis, EventHistory, or list) to a list."""
    if events is None:
        return []
    if isinstance(events, list):
        return events
    for attr in ("events", "history"):
        if hasattr(events, attr):
            return list(getattr(events, attr))
    return []


def _as_block_list(order_blocks) -> list:
    """Normalize Order Blocks (list, OrderBlockMap, or single) to a list."""
    if order_blocks is None:
        return []
    if isinstance(order_blocks, list):
        return order_blocks
    for attr in ("all", "bullish", "bearish"):
        if hasattr(order_blocks, attr):
            return list(getattr(order_blocks, attr))
    return []


def _as_level_list(liquidity) -> list:
    """Normalize a liquidity map / list to a flat level list."""
    if liquidity is None:
        return []
    if isinstance(liquidity, list):
        return liquidity
    for attr in ("levels", "active_levels"):
        if hasattr(liquidity, attr):
            return list(getattr(liquidity, attr))
    return []


def _overlaps(gap_low: float, gap_high: float, block) -> bool:
    """Return True when a block's price range overlaps the gap."""
    b_high = getattr(block, "high", None)
    b_low = getattr(block, "low", None)
    if b_high is None or b_low is None:
        return False
    return float(b_low) <= gap_high and float(b_high) >= gap_low


__all__ = ["ImbalanceMap", "ImbalanceEngine"]
