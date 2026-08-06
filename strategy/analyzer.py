"""Strategy Analyzer — the public façade for the Week 7 Strategy Engine.

``StrategyAnalyzer.analyze(df, structure, liquidity, events, order_blocks,
imbalances)`` combines the full detection pipeline (Weeks 2-6) into ranked,
scored trade setups and a final :class:`TradeDecision`.

This module answers the Week 7 question: **"Should I prepare a trade?"** It
does **not** execute anything — execution is Week 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd

from strategy.confluence import ConfluenceEngine
from strategy.enums import DecisionStatus, SignalDirection
from strategy.filters import StrategyFilters
from strategy.higher_timeframe import HigherTimeframeAnalyzer
from strategy.models import StrategyResult, TradeDecision, TradeZone
from strategy.scoring import ConfluenceScorer, DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS
from strategy.trade_zone import TradeZoneBuilder

from liquidity.models import LiquidityMap
from smart_money.imbalance import ImbalanceMap
from smart_money.models import SmartMoneyAnalysis
from smart_money.order_block_models import OrderBlockMap
from structure.models import MarketStructure


@dataclass(slots=True)
class StrategyAnalyzer:
    """High-level orchestrator for strategy setup generation.

    Attributes:
        timeframe: Label attached to setups.
        builder: The :class:`TradeZoneBuilder`.
        confluence: The :class:`ConfluenceEngine` decision maker.
        filters: The :class:`StrategyFilters` gate.
        higher_timeframe: The HTF bias analyzer.
    """

    timeframe: str = field(default="", kw_only=True)
    builder: TradeZoneBuilder = field(default_factory=TradeZoneBuilder)
    confluence: ConfluenceEngine = field(default_factory=ConfluenceEngine)
    filters: StrategyFilters = field(default_factory=StrategyFilters)
    higher_timeframe: HigherTimeframeAnalyzer = field(
        default_factory=HigherTimeframeAnalyzer
    )

    def __init__(
        self,
        timeframe: str = "",
        weights: Mapping[str, float] | None = None,
        thresholds: Mapping[str, float] | None = None,
        builder: TradeZoneBuilder | None = None,
        filters: StrategyFilters | None = None,
        higher_timeframe: HigherTimeframeAnalyzer | None = None,
    ):
        self.timeframe = timeframe
        scorer = ConfluenceScorer(
            weights=weights or DEFAULT_WEIGHTS,
            thresholds=thresholds or DEFAULT_THRESHOLDS,
        )
        self.confluence = ConfluenceEngine(scorer=scorer, timeframe=timeframe)
        self.builder = builder or TradeZoneBuilder(timeframe=timeframe)
        self.filters = filters or StrategyFilters()
        self.higher_timeframe = higher_timeframe or HigherTimeframeAnalyzer()

    def analyze(
        self,
        df: pd.DataFrame,
        structure: MarketStructure,
        liquidity: LiquidityMap,
        events: SmartMoneyAnalysis,
        order_blocks: OrderBlockMap,
        imbalances: ImbalanceMap,
        htf_bias: str = "NEUTRAL",
        htf_structure=None,
        entry_price: float | None = None,
    ) -> StrategyResult:
        """Analyze the full pipeline and produce a strategy decision.

        Args:
            df: OHLCV candle DataFrame.
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.
            events: Structural events from the Week 4 engine.
            order_blocks: Order block map from the Week 5 engine.
            imbalances: Imbalance (FVG) map from the Week 6 engine.
            htf_bias: Higher-timeframe bias string.
            htf_structure: Optional higher-timeframe MarketStructure used to
                derive the bias when ``htf_bias`` is "NEUTRAL".
            entry_price: Optional explicit entry price. When omitted, the
                latest close is used.

        Returns:
            A :class:`StrategyResult` with ranked zones and a decision.
        """
        if htf_bias == "NEUTRAL" and htf_structure is not None:
            htf_bias = self.higher_timeframe.bias_from_structure(htf_structure)

        entry = entry_price if entry_price is not None else self._entry_price(df)
        prev_close = self._entry_price(df)

        # Build both a bullish and a bearish candidate setup.
        zones: list[TradeZone] = []
        for direction in (SignalDirection.BUY, SignalDirection.SELL):
            zone = self.builder.build(
                direction=direction,
                structure=structure,
                liquidity=liquidity,
                events=events,
                order_blocks=order_blocks,
                imbalances=imbalances,
                entry_price=entry,
                reference_price=prev_close,
            )
            decision = self.confluence.decide(
                direction=direction,
                structure=structure,
                liquidity=liquidity,
                events=events,
                order_blocks=order_blocks,
                imbalances=imbalances,
                entry_price=entry,
                stop_loss=zone.stop_loss,
                target=zone.target,
                swing_high=self._swing_high(structure),
                swing_low=self._swing_low(structure),
                htf_bias=htf_bias,
                order_block=zone.order_block,
                fair_value_gap=zone.fair_value_gap,
                liquidity_level=zone.liquidity,
                structure_event=zone.structure_event,
                setup_type=zone.status,
            )
            # Carry the scored setup into the zone.
            zone.confluence_score = decision.confidence
            zone.reason = decision.reason
            zone.higher_timeframe_bias = htf_bias
            if self.filters.passes(
                zone,
                htf_bias=htf_bias,
                liquidity_swept=self._has_sweep(liquidity),
            ):
                zones.append(zone)

        # Rank by confluence descending.
        zones.sort(key=lambda z: z.confluence_score, reverse=True)

        decision = self._decide(zones)
        return StrategyResult(
            zones=zones,
            timeframe=self.timeframe,
            decision=decision,
        )

    # --- decision helpers --------------------------------------
    def _decide(self, zones: list[TradeZone]) -> TradeDecision:
        """Produce the final decision from the best tradeable zone."""
        best = zones[0] if zones else None
        if best is None or best.confluence_score < 70:
            return TradeDecision(
                status=DecisionStatus.IGNORE,
                confidence=self._best_score(zones),
                direction=SignalDirection.NO_TRADE,
                reason="No tradeable setup — confidence below threshold.",
            )
        return TradeDecision(
            status=self.confluence.scorer.status(best.confluence_score),
            confidence=best.confluence_score,
            direction=best.direction,
            reason=best.reason,
            zone=best,
        )

    def _best_score(self, zones: list[TradeZone]) -> float:
        return zones[0].confluence_score if zones else 0.0

    # --- helpers -----------------------------------------------
    def _entry_price(self, df: pd.DataFrame) -> float:
        if df is None or df.empty:
            return 0.0
        return float(df["close"].iloc[-1])

    def _swing_high(self, structure: MarketStructure) -> float:
        swings = getattr(structure, "swings", None) or []
        highs = [s.price for s in swings if getattr(s, "is_high", False)]
        return max(highs) if highs else 0.0

    def _swing_low(self, structure: MarketStructure) -> float:
        swings = getattr(structure, "swings", None) or []
        lows = [s.price for s in swings if not getattr(s, "is_high", False)]
        return min(lows) if lows else 0.0

    def _has_sweep(self, liquidity: LiquidityMap) -> bool:
        swept = getattr(liquidity, "swept_levels", None)
        if swept is None and hasattr(liquidity, "sweeps"):
            swept = getattr(liquidity, "sweeps", None)
        return bool(swept) if swept is not None else False


__all__ = ["StrategyAnalyzer"]
