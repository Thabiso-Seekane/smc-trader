"""Trade Zone Engine — the public façade for the Trade Zone abstraction.

``TradeZoneEngine.analyze(order_blocks, liquidity, events)`` aggregates the
Week 5 Order Blocks, Week 3 liquidity, and Week 4 structural events into a
list of :class:`TradeZone` objects, scores each by confluence, and returns a
:class:`TradeZoneMap`.

The engine is designed so the Week 7 Confluence Engine simply evaluates
``TradeZone`` objects instead of merging unrelated structures on the fly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from smart_money.confluence import ConfluenceScorer
from smart_money.enums import OrderBlockType
from smart_money.fair_value_gap import FairValueGap
from smart_money.order_block_models import OrderBlock
from smart_money.trade_zone_models import TradeZone, TradeZoneMap


@dataclass(slots=True)
class TradeZoneEngine:
    """High-level orchestrator for Trade Zone aggregation.

    Attributes:
        timeframe: Label attached to detected zones.
        scorer: The :class:`ConfluenceScorer` used to rank zones.
    """

    timeframe: str = field(default="", kw_only=True)
    scorer: ConfluenceScorer = field(default_factory=ConfluenceScorer)

    def analyze(
        self,
        order_blocks,
        liquidity=None,
        events=None,
        fair_value_gaps=None,
    ) -> TradeZoneMap:
        """Aggregate Order Blocks, liquidity, events, and FVGs into Trade Zones.

        Each Order Block becomes the anchor of a Trade Zone. Nearby liquidity
        levels and structural events are attached based on price overlap and
        directional alignment. Fair Value Gaps may be attached if provided
        (Week 6 populates these).

        Args:
            order_blocks: Order Blocks (list, OrderBlockMap, or single block).
            liquidity: Liquidity map whose levels are attached to zones.
            events: Structural events (list, SmartMoneyAnalysis, EventHistory).
            fair_value_gaps: Fair Value Gaps to attach to zones (Week 6).

        Returns:
            A :class:`TradeZoneMap` with bullish/bearish zones ranked by
            confluence.
        """
        blocks = self._as_block_list(order_blocks)
        liquidity_levels = self._as_level_list(liquidity)
        event_list = self._as_event_list(events)
        fvgs = self._as_fvg_list(fair_value_gaps)

        zones: list[TradeZone] = []
        for block in blocks:
            zone = self._build_zone(
                block, liquidity_levels, event_list, fvgs
            )
            zones.append(self.scorer.score(zone))

        return self._build_map(zones)

    def analyze_multi(
        self,
        order_blocks_by_tf: dict[str, object],
        liquidities: dict[str, object] | None = None,
        events_by_tf: dict[str, object] | None = None,
        fvgs_by_tf: dict[str, object] | None = None,
    ) -> TradeZoneMap:
        """Aggregate Trade Zones across multiple timeframes and merge them.

        Args:
            order_blocks_by_tf: Mapping of ``timeframe_label -> Order Blocks``.
            liquidities: Mapping of ``timeframe_label -> LiquidityMap``.
            events_by_tf: Mapping of ``timeframe_label -> events``.
            fvgs_by_tf: Mapping of ``timeframe_label -> FairValueGaps``.

        Returns:
            A merged :class:`TradeZoneMap` with all timeframe zones, ranked
            across the combined set.
        """
        zones: list[TradeZone] = []
        for tf, blocks in order_blocks_by_tf.items():
            self.timeframe = tf
            mapped = self.analyze(
                order_blocks=blocks,
                liquidity=(liquidities or {}).get(tf),
                events=(events_by_tf or {}).get(tf, []),
                fair_value_gaps=(fvgs_by_tf or {}).get(tf, []),
            )
            zones.extend(mapped.all)

        ranked = self.scorer.rank(zones)
        return self._build_map(ranked)

    def _build_zone(
        self,
        block: OrderBlock,
        liquidity_levels: list[object],
        event_list: list[object],
        fvgs: list[FairValueGap],
    ) -> TradeZone:
        """Build a Trade Zone anchored by a single Order Block."""
        direction = (
            OrderBlockType.BULLISH
            if getattr(block, "is_bullish", False)
            else OrderBlockType.BEARISH
        )
        high = float(getattr(block, "high", 0.0))
        low = float(getattr(block, "low", 0.0))
        origin_time = getattr(block, "origin_time", datetime.now())

        # Attach liquidity levels that overlap the zone.
        overlapping_levels = [
            level
            for level in liquidity_levels
            if self._level_overlaps(level, low, high)
        ]

        # Attach events that share the same direction.
        matching_events = [
            event for event in event_list if self._event_matches(event, direction)
        ]

        return TradeZone(
            direction=direction,
            high=high,
            low=low,
            origin_time=origin_time,
            order_block=block,
            fair_value_gaps=fvgs,
            liquidity_levels=overlapping_levels,
            events=matching_events,
            timeframe=self.timeframe,
            active=getattr(block, "is_active", True),
            mitigated=getattr(block, "mitigated", False),
            invalidated=getattr(block, "invalidated", False),
        )

    def _level_overlaps(self, level, low: float, high: float) -> bool:
        """Return True when a liquidity level's price overlaps the zone."""
        price = getattr(level, "price", None)
        if price is None:
            return False
        return low <= float(price) <= high

    def _event_matches(self, event, direction: OrderBlockType) -> bool:
        """Return True when an event's direction aligns with the zone."""
        is_bullish = getattr(event, "is_bullish", None)
        if is_bullish is None:
            return False
        return is_bullish == (direction == OrderBlockType.BULLISH)

    def _build_map(self, zones: list[TradeZone]) -> TradeZoneMap:
        """Aggregate scored zones into a map."""
        bullish = [z for z in zones if z.is_bullish]
        bearish = [z for z in zones if z.is_bearish]
        active = [z for z in zones if z.is_active]
        return TradeZoneMap(
            bullish=bullish,
            bearish=bearish,
            active=active,
            timeframe=self.timeframe,
        )

    # --- normalizers -----------------------------------------
    def _as_block_list(self, order_blocks) -> list[OrderBlock]:
        """Normalize Order Blocks (list, OrderBlockMap, or single) to a list."""
        if order_blocks is None:
            return []
        if isinstance(order_blocks, OrderBlock):
            return [order_blocks]
        if isinstance(order_blocks, list):
            return order_blocks
        for attr in ("all", "bullish", "bearish"):
            if hasattr(order_blocks, attr):
                return list(getattr(order_blocks, attr))
        return []

    def _as_level_list(self, liquidity) -> list[object]:
        """Normalize a liquidity map / list to a flat level list."""
        if liquidity is None:
            return []
        if isinstance(liquidity, list):
            return liquidity
        for attr in ("levels", "active_levels"):
            if hasattr(liquidity, attr):
                return list(getattr(liquidity, attr))
        return []

    def _as_event_list(self, events) -> list[object]:
        """Normalize events (list, SmartMoneyAnalysis, EventHistory) to a list."""
        if events is None:
            return []
        if isinstance(events, list):
            return events
        for attr in ("events", "history"):
            if hasattr(events, attr):
                return list(getattr(events, attr))
        return []

    def _as_fvg_list(self, fvgs) -> list[FairValueGap]:
        """Normalize Fair Value Gaps to a list."""
        if fvgs is None:
            return []
        if isinstance(fvgs, list):
            return fvgs
        for attr in ("all", "gaps"):
            if hasattr(fvgs, attr):
                return list(getattr(fvgs, attr))
        return []


__all__ = ["TradeZoneEngine"]
