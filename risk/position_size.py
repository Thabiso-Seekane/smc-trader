"""Position sizing for the Week 8 Risk Engine.

This module answers: *"What lot size should I trade?"*

Given the account balance, the percent risk, and the stop distance, it
computes the lot size so that a stop-out loses exactly the intended risk
amount. The execution layer never recalculates this — it reads the lot size
from the plan.
"""

from __future__ import annotations

from dataclasses import dataclass

from risk.account import Account
from risk.enums import PositionSizingMethod
from risk.models import PositionSize


@dataclass(slots=True)
class PositionSizer:
    """Compute lot sizes from a risk budget and stop distance.

    Attributes:
        instrument_joint: Price of one unit/contract of the instrument.
            For forex this is often a fixed contract multiple (e.g. 10 for
            XAUUSD meaning $1 move = $10 per 1.0 lot); for other symbols
            it may be 1.0.
        min_lots: Minimum allowable lot size.
        max_lots: Maximum allowable lot size.
        default_method: Sizing method used when no override is given.
    """

    instrument_joint: float = 10.0
    min_lots: float = 0.01
    max_lots: float = 100.0
    default_method: PositionSizingMethod = PositionSizingMethod.FIXED_FRACTIONAL

    def size(
        self,
        account: Account | None = None,
        *,
        balance: float | None = None,
        risk_percent: float = 1.0,
        stop_distance: float = 1.0,
        risk_amount: float | None = None,
        method: PositionSizingMethod | None = None,
    ) -> PositionSize:
        """Compute the lot size for a trade.

        Args:
            account: Optional :class:`Account`. When given, its balance is
                used as the sizing base.
            balance: Explicit account balance (ignored when ``account`` is
                provided).
            risk_percent: Percent of balance to risk on this trade.
            stop_distance: Stop distance in price units.
            risk_amount: Optional exact currency risk. When provided this
                overrides ``risk_percent`` and uses RISK_BASED sizing.
            method: Sizing method override.

        Returns:
            A :class:`PositionSize`.
        """
        bal = account.balance if account is not None else (balance or 0.0)
        if bal <= 0 or stop_distance <= 0:
            return PositionSize(lots=0.0, method=method or self.default_method)

        sizing_method = method or self.default_method

        if sizing_method == PositionSizingMethod.FIXED_LOT:
            lots = self.min_lots
            risk = self._risk_for_lots(lots, bal, risk_percent, risk_amount)
            return PositionSize(
                lots=lots,
                method=sizing_method,
                risk_amount=risk,
                account_at_risk_pct=(risk / bal * 100.0) if bal > 0 else 0.0,
            )

        if sizing_method == PositionSizingMethod.RISK_BASED and risk_amount is not None:
            budget = risk_amount
            risk_pct = (budget / bal) * 100.0
        else:
            budget = bal * (risk_percent / 100.0)
            risk_pct = risk_percent

        raw = self._to_lots(budget, stop_distance)
        lots = max(self.min_lots, min(self.max_lots, raw))

        return PositionSize(
            lots=lots,
            method=sizing_method,
            risk_amount=budget,
            account_at_risk_pct=risk_pct,
        )

    def _to_lots(self, risk_amount: float, stop_distance: float) -> float:
        """Convert a currency risk budget and stop distance to lot size."""
        if stop_distance <= 0:
            return 0.0
        return risk_amount / (stop_distance * self.instrument_joint)

    def _risk_for_lots(
        self,
        lots: float,
        balance: float,
        risk_percent: float,
        risk_amount: float | None,
    ) -> float:
        """Return the actual currency risk implied by a fixed lot size."""
        if risk_amount is not None:
            return risk_amount
        return balance * (risk_percent / 100.0)

    @property
    def is_valid(self) -> bool:
        """Return True when the sizer is configured sanely."""
        return self.instrument_joint > 0 and self.min_lots > 0 and self.max_lots >= self.min_lots


__all__ = ["PositionSizer"]
