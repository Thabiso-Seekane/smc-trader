"""Enums for the Week 8 Risk & Trading Plan Engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class PositionSizingMethod(str, Enum):
    """How the lot size is derived from the risk budget.

    * ``FIXED_FRACTIONAL`` — risk a fixed percentage of account balance.
    * ``FIXED_LOT`` — trade a fixed lot size regardless of risk per R.
    * ``RISK_BASED`` — risk an exact currency amount per trade.
    """

    FIXED_FRACTIONAL = "FIXED_FRACTIONAL"
    FIXED_LOT = "FIXED_LOT"
    RISK_BASED = "RISK_BASED"


class PlanStatus(str, Enum):
    """Lifecycle state of a TradePlan.

    * ``READY`` — plan is valid and can be executed.
    * ``REJECTED`` — plan failed risk validation and must not be traded.
    * ``EXPIRED`` — plan's expiration time has passed.
    """

    READY = "READY"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RiskStatus(str, Enum):
    """Overall risk posture of a trade plan.

    * ``WITHIN_LIMIT`` — risk is within all configured limits.
    * ``MAX_DRAWDOWN`` — the account is at/beyond max drawdown.
    * ``DAILY_LIMIT`` — the daily loss limit has been reached.
    * ``POSITION_CAP`` — the maximum concurrent positions is reached.
    * ``BLOCKED`` — the account/symbol is blocked from trading.
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    DAILY_LIMIT = "DAILY_LIMIT"
    POSITION_CAP = "POSITION_CAP"
    BLOCKED = "BLOCKED"


class StopLossMode(str, Enum):
    """How the stop-loss is derived from the setup.

    * ``STRUCTURAL`` — use the provided structure stop (swing/OB edge).
    * ``ATR`` — place the stop a fixed multiple of ATR away.
    * ``FIXED_PIPS`` — place the stop a fixed distance in price.
    """

    STRUCTURAL = "STRUCTURAL"
    ATR = "ATR"
    FIXED_PIPS = "FIXED_PIPS"


class TakeProfitMode(str, Enum):
    """How the take-profit is derived from the plan.

    * ``RR_MULTIPLE`` — target at a fixed R-multiple.
    * ``STRUCTURAL`` — target at a structural level (swing/previous high-low).
    * ``FIXED_PIPS`` — target a fixed distance in price.
    """

    RR_MULTIPLE = "RR_MULTIPLE"
    STRUCTURAL = "STRUCTURAL"
    FIXED_PIPS = "FIXED_PIPS"


__all__ = [
    "PositionSizingMethod",
    "PlanStatus",
    "RiskStatus",
    "StopLossMode",
    "TakeProfitMode",
]
