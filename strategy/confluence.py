"""The Week 7 Confluence Engine — the decision-maker.

The ConfluenceEngine consumes the full pipeline (Market Structure, Liquidity,
CHoCH/BOS, Order Blocks, Fair Value Gaps) plus the premium/discount position
and higher-timeframe bias, and produces a :class:`strategy.models.TradeZone`
setup with a 0-100 confluence score.

The scoring is **configuration-driven** (see :class:`ConfluenceScorer`) so
weights and thresholds can be tuned during backtesting without code changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from strategy.enums import (
    PremiumDiscountPosition,
    RiskRewardLevel,
    SetupType,
    SignalDirection,
)
from strategy.higher_timeframe import HigherTimeframeAnalyzer
from strategy.models import TradeZone, TradeDecision
from strategy.premium_discount import PremiumDiscountAnalyzer
from strategy.scoring import ConfluenceScorer, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS


@dataclass(slots=True)
class ConfluenceEngine:
    """Combine all confirmation modules into a trade decision.

    Attributes:
        scorer: The config-driven :class:`ConfluenceScorer`.
        premium_discount: The premium/discount analyzer.
        higher_timeframe: The HTF bias analyzer.
        timeframe: Label attached to setups.
    """

    scorer: ConfluenceScorer = field(default_factory=ConfluenceScorer)
    premium_discount: PremiumDiscountAnalyzer = field(
        default_factory=PremiumDiscountAnalyzer
    )
    higher_timeframe: HigherTimeframeAnalyzer = field(
        default_factory=HigherTimeframeAnalyzer
    )
    timeframe: str = field(default="", kw_only=True)

    def __init__(
        self,
        scorer: ConfluenceScorer | None = None,
        premium_discount: PremiumDiscountAnalyzer | None = None,
        higher_timeframe: HigherTimeframeAnalyzer | None = None,
        timeframe: str = "",
        weights: Mapping[str, float] | None = None,
        thresholds: Mapping[str, float] | None = None,
    ):
        self.scorer = scorer or ConfluenceScorer(
            weights=weights or DEFAULT_WEIGHTS, thresholds=thresholds or DEFAULT_THRESHOLDS
        )
        self.premium_discount = premium_discount or PremiumDiscountAnalyzer()
        self.higher_timeframe = higher_timeframe or HigherTimeframeAnalyzer()
        self.timeframe = timeframe

    def decide(
        self,
        *,
        direction: SignalDirection,
        structure=None,
        liquidity=None,
        events=None,
        order_blocks=None,
        imbalances=None,
        entry_price: float,
        stop_loss: float,
        target: float,
        swing_high: float,
        swing_low: float,
        htf_bias: str = "NEUTRAL",
        order_block=None,
        fair_value_gap=None,
        liquidity_level=None,
        structure_event=None,
        setup_type: SetupType = SetupType.CORE_SETUP,
    ) -> TradeDecision:
        """Build a :class:`TradeDecision` for a single directional setup.

        Args:
            direction: Buy or sell bias.
            structure: The current market structure (Week 2).
            liquidity: The liquidity map (Week 3).
            events: The structural events (Week 4).
            order_blocks: The order block map (Week 5).
            imbalances: The imbalance map / FVGs (Week 6).
            entry_price: Ideal entry price.
            stop_loss: Protective stop.
            target: Profit target.
            swing_high: High of the latest dealing range.
            swing_low: Low of the latest dealing range.
            htf_bias: Higher-timeframe bias ("BULLISH"/"BEARISH"/"NEUTRAL").
            order_block: The anchoring Order Block (optional).
            fair_value_gap: The overlapping FVG (optional).
            liquidity_level: The interacting liquidity level (optional).
            structure_event: The confirming structural event (optional).
            setup_type: Kind of setup.

        Returns:
            A :class:`TradeDecision` with the computed confidence.
        """
        available = self._available_factors(
            direction=direction,
            liquidity=liquidity,
            events=events,
            order_blocks=order_blocks,
            imbalances=imbalances,
            entry_price=entry_price,
            swing_high=swing_high,
            swing_low=swing_low,
            htf_bias=htf_bias,
            stop_loss=stop_loss,
            target=target,
        )
        confidence = self.scorer.score(available)
        status = self.scorer.status(confidence)

        position = self.premium_discount.analyze(
            entry_price, swing_high, swing_low
        )
        risk_reward = self._risk_reward_level(entry_price, stop_loss, target)

        reason = self._build_reason(available, confidence, direction)

        zone = TradeZone(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            confluence_score=confidence,
            order_block=order_block,
            fair_value_gap=fair_value_gap,
            liquidity=liquidity_level,
            structure_event=structure_event,
            higher_timeframe_bias=htf_bias,
            premium_discount=position,
            risk_reward=risk_reward,
            status=setup_type,
            timeframe=self.timeframe,
            reason=reason,
        )

        return TradeDecision(
            status=status,
            confidence=confidence,
            direction=direction,
            reason=reason,
            zone=zone,
        )

    # --- internal helpers --------------------------------------
    def _available_factors(
        self,
        *,
        direction: SignalDirection,
        liquidity,
        events,
        order_blocks,
        imbalances,
        entry_price: float,
        swing_high: float,
        swing_low: float,
        htf_bias: str,
        stop_loss: float,
        target: float,
    ) -> set[str]:
        """Compute the set of confirmation factors present for a setup."""
        available: set[str] = set()

        if self.higher_timeframe.score(htf_bias, direction) >= 100.0:
            available.add("higher_timeframe")
        if self.scorer.liquidity_sweep_present(liquidity):
            available.add("liquidity_sweep")
        if self.scorer.choch_present(events):
            available.add("choch")
        if self.scorer.bos_present(events):
            available.add("bos")
        if self.scorer.order_block_present(order_blocks):
            available.add("order_block")
        if self.scorer.fvg_present(imbalances):
            available.add("fair_value_gap")

        position = self.premium_discount.analyze(
            entry_price, swing_high, swing_low
        )
        if self.scorer.premium_discount_aligned(position, direction):
            available.add("premium_discount")

        if self._has_risk_reward(stop_loss, target, entry_price):
            available.add("risk_reward")

        return available

    def _has_risk_reward(self, stop_loss: float, target: float, entry: float) -> bool:
        """Return True when the setup has a reward of 1R+."""
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        if risk <= 0:
            return False
        return reward >= risk

    def _risk_reward_level(
        self, entry: float, stop: float, target: float
    ) -> RiskRewardLevel:
        """Classify the risk/reward level from the setup geometry."""
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if risk <= 0:
            return RiskRewardLevel.NONE
        ratio = reward / risk
        if ratio >= 3.0:
            return RiskRewardLevel.EXCELLENT
        if ratio >= 2.0:
            return RiskRewardLevel.GOOD
        if ratio >= 1.0:
            return RiskRewardLevel.FAIR
        return RiskRewardLevel.POOR

    def _build_reason(
        self, available: set[str], confidence: float, direction: SignalDirection
    ) -> str:
        """Build a human-readable summary of the confirmation factors."""
        if direction == SignalDirection.NO_TRADE:
            return f"No trade — confidence {confidence:.0f}"
        label = "Bullish" if direction == SignalDirection.BUY else "Bearish"
        factors = ", ".join(sorted(available)) if available else "—"
        return f"{label} setup ({factors}) — confidence {confidence:.0f}"


__all__ = ["ConfluenceEngine"]
