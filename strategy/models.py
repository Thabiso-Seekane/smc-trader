"""Data models for the Week 7 Strategy Engine.

This module contains only data models (dataclasses) and holds no business
logic. The strategy engine consumes the outputs of Weeks 2-6 and produces
:class:`TradeZone` setups and :class:`TradeDecision` results.

The :class:`TradeZone` here is a **richer** model than the Week 5b
``smart_money.TradeZone``. It represents a complete, executable trading
opportunity with entry/stop/target geometry, a confluence score, and the
individual confirmation factors that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from strategy.enums import (
    DecisionStatus,
    PremiumDiscountPosition,
    RiskRewardLevel,
    SetupType,
    SignalDirection,
)


@dataclass(slots=True)
class TradeZone:
    """A complete, prepared trading opportunity.

    Attributes:
        direction: Buy or sell bias of the setup.
        entry_price: Ideal entry price for the setup.
        stop_loss: Protective stop-loss price.
        target: Profit target price.
        confluence_score: 0-100 aggregate confluence score.
        order_block: The anchoring Order Block (optional).
        fair_value_gap: The overlapping Fair Value Gap (optional).
        liquidity: The interacting liquidity level (optional).
        structure_event: The confirming CHoCH/BOS event (optional).
        higher_timeframe_bias: HTF alignment (bullish/bearish/neutral).
        premium_discount: Where price sits relative to equilibrium.
        risk_reward: Quality of the available risk/reward.
        status: Setup type (core / early / reconfirmation).
        id: Unique identifier for the zone.
        timeframe: Label of the timeframe the setup was derived from.
        reason: Human-readable summary of why the engine likes this setup.
    """

    direction: SignalDirection
    entry_price: float
    stop_loss: float
    target: float
    confluence_score: float = 0.0
    order_block: object | None = None
    fair_value_gap: object | None = None
    liquidity: object | None = None
    structure_event: object | None = None
    higher_timeframe_bias: str = "NEUTRAL"
    premium_discount: PremiumDiscountPosition = PremiumDiscountPosition.EQUILIBRIUM
    risk_reward: RiskRewardLevel = RiskRewardLevel.NONE
    status: SetupType = SetupType.CORE_SETUP
    id: UUID = field(default_factory=uuid4)
    timeframe: str = ""
    reason: str = ""

    # --- directional helpers -----------------------------------
    @property
    def is_buy(self) -> bool:
        """Return True when this is a buy (long) setup."""
        return self.direction == SignalDirection.BUY

    @property
    def is_sell(self) -> bool:
        """Return True when this is a sell (short) setup."""
        return self.direction == SignalDirection.SELL

    # --- geometry helpers --------------------------------------
    @property
    def risk(self) -> float:
        """Return the risk distance (entry-to-stop) in price units."""
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward(self) -> float:
        """Return the reward distance (entry-to-target) in price units."""
        return abs(self.target - self.entry_price)

    @property
    def risk_reward_ratio(self) -> float:
        """Return the reward-to-risk ratio (0.0 when risk is zero)."""
        if self.risk <= 0:
            return 0.0
        return self.reward / self.risk

    @property
    def is_valid(self) -> bool:
        """Return True when the setup has a valid risk/reward geometry.

        A buy is valid when target > entry > stop; a sell is valid when
        target < entry < stop.
        """
        if self.risk <= 0:
            return False
        if self.is_buy:
            return self.target > self.entry_price > self.stop_loss
        if self.is_sell:
            return self.target < self.entry_price < self.stop_loss
        return False

    def __hash__(self) -> int:
        """Hash by zone identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class TradeDecision:
    """The final strategy decision for a trade zone.

    This is the *preparation* answer — not an execution order. It tells the
    caller whether a setup is worth preparing and how confident the engine
    is.

    Attributes:
        status: Quality tier derived from the confidence score.
        confidence: 0-100 confluence confidence.
        direction: Buy / sell / no-trade bias.
        reason: Human-readable summary used for debugging.
        zone: The underlying :class:`TradeZone` setup (optional).
    """

    status: DecisionStatus
    confidence: float
    direction: SignalDirection = SignalDirection.NO_TRADE
    reason: str = ""
    zone: TradeZone | None = None

    @property
    def is_valid(self) -> bool:
        """Return True when the decision is tradeable (not IGNORE)."""
        return self.status != DecisionStatus.IGNORE

    @property
    def is_excellent(self) -> bool:
        """Return True when confidence is in the excellent range."""
        return self.status == DecisionStatus.EXCELLENT

    @property
    def is_strong(self) -> bool:
        """Return True when confidence is in the strong range."""
        return self.status == DecisionStatus.STRONG

    @property
    def is_acceptable(self) -> bool:
        """Return True when confidence is in the acceptable range."""
        return self.status == DecisionStatus.ACCEPTABLE


@dataclass(slots=True)
class StrategyResult:
    """The aggregated output of the Week 7 Strategy Analyzer.

    This is the object returned by ``StrategyAnalyzer.analyze(...)``. It
    holds all ranked setups plus the best validated one.

    Attributes:
        zones: All ranked trade zones (best first).
        timeframe: Label of the strategy timeframe.
        decision: The final :class:`TradeDecision` for the best setup.
    """

    zones: list[TradeZone] = field(default_factory=list)
    timeframe: str = ""
    decision: TradeDecision | None = None

    @property
    def best(self) -> TradeZone | None:
        """Return the highest-confluence valid zone, if any."""
        valid = [z for z in self.zones if z.is_valid]
        if not valid:
            return None
        best = max(valid, key=lambda z: z.confluence_score)
        if best.confluence_score < 70:
            return None
        return best

    @property
    def tradeable(self) -> list[TradeZone]:
        """Return all zones with a confluence score of 70+ (tradeable)."""
        return [z for z in self.zones if z.confluence_score >= 70]

    @property
    def count(self) -> int:
        """Return the total number of zones."""
        return len(self.zones)

    def __len__(self) -> int:
        return self.count


__all__ = ["TradeZone", "TradeDecision", "StrategyResult"]
