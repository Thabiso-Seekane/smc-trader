"""Data models for the Week 8 Risk & Trading Plan Engine.

This module contains only data models (dataclasses) and holds no business
logic. The risk engine converts a Week 7 :class:`strategy.models.TradeZone`
into a complete :class:`TradePlan` with position sizing, stop/target
placement, risk metrics, and projected P&L.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from risk.enums import PlanStatus, PositionSizingMethod, RiskStatus


@dataclass(slots=True)
class PositionSize:
    """The computed lot / unit size for a trade plan.

    Attributes:
        lots: The lot size (or units) derived from the risk budget.
        method: How the size was derived.
        risk_amount: The currency amount at risk on the trade.
        account_at_risk_pct: Percentage of the account balance at risk.
    """

    lots: float = 0.0
    method: PositionSizingMethod = PositionSizingMethod.FIXED_FRACTIONAL
    risk_amount: float = 0.0
    account_at_risk_pct: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Return True when a positive lot size was computed."""
        return self.lots > 0.0


@dataclass(slots=True)
class RiskMetrics:
    """Aggregate risk-related measurements for a trade plan.

    Attributes:
        account_balance: Current account balance (or equity).
        risk_percent: The target per-trade risk as a percentage.
        risk_amount: The currency amount at risk on the trade.
        position_size: The computed position size.
        daily_risk_used_pct: Daily risk consumed so far.
        max_daily_risk_pct: The configured daily risk limit.
        status: Overall risk posture.
    """

    account_balance: float = 0.0
    risk_percent: float = 1.0
    risk_amount: float = 0.0
    position_size: PositionSize = field(default_factory=PositionSize)
    daily_risk_used_pct: float = 0.0
    max_daily_risk_pct: float = 3.0
    status: RiskStatus = RiskStatus.WITHIN_LIMIT


@dataclass(slots=True)
class TradePlan:
    """A complete, risk-managed trading plan.

    This is the output of the Week 8 Risk Engine. The execution layer (a
    later week) consumes only this object — it never recalculates stops,
    lot sizes, or risk. It simply reads the plan and places orders.

    Attributes:
        id: Unique identifier for the plan.
        symbol: Trading symbol (e.g. "XAUUSD").
        direction: Buy/sell bias (string label).
        entry_price: Ideal entry price.
        instrument_joint: Price of one unit (for lot conversion).
        stop_loss: Placement of the protective stop.
        take_profit: Placement of the profit target.
        risk_reward: Reward-to-risk ratio.
        rolling_stop: Whether the stop trails the price (optional).
        breakout_size: Optional reference for placement.
        expiration: Timestamp after which the plan expires.
        timeframe: Timeframe the setup was derived from.
        position_size: The computed position size.
        risk: Risk distance / amount.
        reward: Reward distance / amount.
        confidence: 0-100 confluence confidence (from Week 7).
        status: Whether the plan is READY / REJECTED / EXPIRED.
        risk_metrics: The aggregated risk metrics.
        created_at: When the plan was built.
        note: Human-readable summary / reason.
    """

    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    direction: str = "BUY"
    entry_price: float = 0.0
    instrument_joint: float = 1.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_reward: float = 0.0
    rolling_stop: bool = False
    breakout_size: float = 0.0
    expiration: datetime | None = None
    timeframe: str = ""
    position_size: PositionSize = field(default_factory=PositionSize)
    risk: float = 0.0
    reward: float = 0.0
    confidence: float = 0.0
    status: PlanStatus = PlanStatus.READY
    risk_metrics: RiskMetrics = field(default_factory=RiskMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    note: str = ""

    # --- geometry helpers ------------------------------------
    @property
    def is_buy(self) -> bool:
        """Return True when this is a buy (long) plan."""
        return self.direction.upper() == "BUY"

    @property
    def is_sell(self) -> bool:
        """Return True when this is a sell (short) plan."""
        return self.direction.upper() == "SELL"

    @property
    def risk_distance(self) -> float:
        """Return the stop distance in price units."""
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_distance(self) -> float:
        """Return the target distance in price units."""
        return abs(self.take_profit - self.entry_price)

    @property
    def risk_reward_ratio(self) -> float:
        """Return the reward-to-risk ratio (0.0 when risk is zero)."""
        if self.risk_distance <= 0:
            return 0.0
        return self.reward_distance / self.risk_distance

    @property
    def is_ready(self) -> bool:
        """Return True when the plan is valid and can be executed."""
        if self.status != PlanStatus.READY:
            return False
        if not self.position_size.is_valid:
            return False
        if self.entry_price <= 0 or self.stop_loss <= 0 or self.take_profit <= 0:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Return True when the plan has passed its expiration time."""
        if self.expiration is None:
            return False
        return datetime.now() >= self.expiration

    @property
    def is_risk_valid(self) -> bool:
        """Return True when the risk metrics are within configured limits."""
        return self.risk_metrics.status == RiskStatus.WITHIN_LIMIT

    # --- P&L helpers -----------------------------------------
    @property
    def stop_loss_amount(self) -> float:
        """Return the money lost if stopped out (negative)."""
        if not self.position_size.is_valid:
            return -(self.risk_amount)
        return -self.risk_metrics.risk_amount

    @property
    def take_profit_amount(self) -> float:
        """Return the money made if the target is hit (positive)."""
        if not self.position_size.is_valid:
            return 0.0
        return self.risk_metrics.risk_amount * self.risk_reward_ratio

    # --- R-multiple table ------------------------------------
    def pnl_at_r(self, r_multiple: float) -> float:
        """Project P&L (in currency) for a given R-multiple outcome.

        A negative R-multiple is a loss, a positive one is a gain. With a
        risk amount of 100.0: ``pnl_at_r(-1) == -100``, ``pnl_at_r(2) == 200``.
        """
        return self.risk_metrics.risk_amount * r_multiple

    def __hash__(self) -> int:
        """Hash by plan identity (id)."""
        return hash(self.id)


__all__ = ["PositionSize", "RiskMetrics", "TradePlan"]
