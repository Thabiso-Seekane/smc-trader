"""Account model for the Week 8 Risk Engine.

This module holds the :class:`Account` used to track balance, equity, open
risk, and daily/monthly drawdown. It is the source of truth for whether a
trade may be taken given the account's risk posture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from risk.enums import RiskStatus


@dataclass(slots=True)
class Account:
    """A trading account with balance/equity and risk limits.

    Attributes:
        balance: Current account balance (cash).
        equity: Current account equity (balance +/- open P&L).
        initial_balance: Opening balance used to measure drawdown.
        max_drawdown_pct: Maximum allowed drawdown of initial balance.
        max_daily_risk_pct: Maximum daily risk (loss) as % of balance.
        max_open_positions: Maximum concurrent positions allowed.
        open_positions: Number of currently open positions.
        daily_loss: Realized loss so far today.
        blocked: When True, the account is frozen from trading.
    """

    balance: float = 10000.0
    equity: float = 10000.0
    initial_balance: float = 10000.0
    max_drawdown_pct: float = 20.0
    max_daily_risk_pct: float = 3.0
    max_open_positions: int = 5
    open_positions: int = 0
    daily_loss: float = 0.0
    blocked: bool = False

    # --- derived risk posture --------------------------------
    @property
    def drawdown_pct(self) -> float:
        """Return the current drawdown as a percentage of initial balance."""
        if self.initial_balance <= 0:
            return 0.0
        return (1.0 - self.equity / self.initial_balance) * 100.0

    @property
    def daily_risk_pct(self) -> float:
        """Return the daily loss already consumed as % of balance."""
        if self.balance <= 0:
            return 0.0
        return (self.daily_loss / self.balance) * 100.0

    @property
    def status(self) -> RiskStatus:
        """Return the account-wide risk posture."""
        if self.blocked:
            return RiskStatus.BLOCKED
        if self.drawdown_pct >= self.max_drawdown_pct:
            return RiskStatus.MAX_DRAWDOWN
        if self.daily_risk_pct >= self.max_daily_risk_pct:
            return RiskStatus.DAILY_LIMIT
        if self.open_positions >= self.max_open_positions:
            return RiskStatus.POSITION_CAP
        return RiskStatus.WITHIN_LIMIT

    # --- queries ---------------------------------------------
    @property
    def can_trade(self) -> bool:
        """Return True when the account permits taking a new trade."""
        return self.status == RiskStatus.WITHIN_LIMIT

    def risk_amount_for(self, risk_percent: float) -> float:
        """Return the currency at risk for a given percent-of-balance risk."""
        if risk_percent <= 0:
            return 0.0
        return self.balance * (risk_percent / 100.0)

    def available_positions(self) -> int:
        """Return how many more positions the account may open."""
        return max(0, self.max_open_positions - self.open_positions)


__all__ = ["Account"]
