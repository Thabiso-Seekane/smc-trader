"""Enums for the Week 7 Strategy Engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class SignalDirection(str, Enum):
    """Directional bias of a prepared trade setup.

    * ``BUY`` — long bias (bullish confluence).
    * ``SELL`` — short bias (bearish confluence).
    * ``NO_TRADE`` — no acceptable setup (confidence below threshold).
    """

    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class DecisionStatus(str, Enum):
    """Quality tier of a :class:`TradeDecision`.

    * ``EXCELLENT`` — 90+ confluence.
    * ``STRONG`` — 80-89 confluence.
    * ``ACCEPTABLE`` — 70-79 confluence.
    * ``IGNORE`` — below 70 confluence (do not trade).
    """

    EXCELLENT = "EXCELLENT"
    STRONG = "STRONG"
    ACCEPTABLE = "ACCEPTABLE"
    IGNORE = "IGNORE"


class SetupType(str, Enum):
    """Kind of price-action setup backing a trade zone.

    * ``CORE_SETUP`` — a fully-aligned, high-confluence setup.
    * ``EARLY_ENTRY`` — a setup that is forming but not yet confirmed.
    * ``RECONFIRMATION`` — a previously-valid setup that re-confirmed.
    """

    CORE_SETUP = "CORE_SETUP"
    EARLY_ENTRY = "EARLY_ENTRY"
    RECONFIRMATION = "RECONFIRMATION"


class PremiumDiscountPosition(str, Enum):
    """Where a price sits relative to equilibrium of the dealing range.

    * ``PREMIUM`` — above equilibrium (expensive; favour sell-side).
    * ``DISCOUNT`` — below equilibrium (cheap; favour buy-side).
    * ``EQUILIBRIUM`` — at the 50% mark (neutral).
    """

    PREMIUM = "PREMIUM"
    DISCOUNT = "DISCOUNT"
    EQUILIBRIUM = "EQUILIBRIUM"


class RiskRewardLevel(str, Enum):
    """Quality of the available risk/reward for a setup.

    * ``NONE`` — no valid geometry (no stop/target).
    * ``POOR`` — reward is less than 1R.
    * ``FAIR`` — reward is 1R-2R.
    * ``GOOD`` — reward is 2R-3R.
    * ``EXCELLENT`` — reward is 3R+.
    """

    NONE = "NONE"
    POOR = "POOR"
    FAIR = "FAIR"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"


__all__ = [
    "SignalDirection",
    "DecisionStatus",
    "SetupType",
    "PremiumDiscountPosition",
    "RiskRewardLevel",
]
