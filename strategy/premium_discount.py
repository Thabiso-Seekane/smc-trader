"""Premium / Discount analyzer.

One of the core SMC concepts is that price is either **expensive** (above
equilibrium — *premium*) or **cheap** (below equilibrium — *discount*)
relative to the latest dealing range. Institutions prefer to buy in
discount and sell in premium, so a setup that aligns with the correct
premium/discount region scores higher.

This module computes equilibrium from the latest dealing range (a swing
high → swing low) and classifies any price into PREMIUM / DISCOUNT /
EQUILIBRIUM.
"""

from __future__ import annotations

from dataclasses import dataclass

from strategy.enums import PremiumDiscountPosition, SignalDirection


@dataclass(slots=True)
class PremiumDiscountAnalyzer:
    """Classify prices relative to the equilibrium of a dealing range.

    Attributes:
        premium_start: Confluence added when a bearish / sell setup sits in
            premium (0-100).
        discount_start: Score when price is at the extreme discount.
    """

    premium_start: float = 100.0
    discount_start: float = 100.0

    def analyze(self, price: float, swing_high: float, swing_low: float) -> PremiumDiscountPosition:
        """Classify ``price`` relative to the dealing range.

        Args:
            price: The price to classify.
            swing_high: The high of the latest dealing range.
            swing_low: The low of the latest dealing range.

        Returns:
            PREMIUM when above equilibrium, DISCOUNT when below, and
            EQUILIBRIUM when at the 50% mark.
        """
        eq = self.equilibrium(swing_high, swing_low)
        if price > eq:
            return PremiumDiscountPosition.PREMIUM
        if price < eq:
            return PremiumDiscountPosition.DISCOUNT
        return PremiumDiscountPosition.EQUILIBRIUM

    def equilibrium(self, swing_high: float, swing_low: float) -> float:
        """Return the 50% equilibrium price of the dealing range."""
        return (swing_high + swing_low) / 2.0

    def score(
        self,
        position: PremiumDiscountPosition,
        direction: SignalDirection,
    ) -> float:
        """Return a 0-100 congruence score for a setup.

        A bullish setup scores highest in discount; a bearish setup scores
        highest in premium. A mismatch (bullish in premium) scores low.

        Args:
            position: The premium/discount classification of the entry.
            direction: The direction of the setup.

        Returns:
            0-100 score where 100 is a perfect premium/discount match.
        """
        if position == PremiumDiscountPosition.EQUILIBRIUM:
            return 50.0
        if direction == SignalDirection.BUY:
            return self.discount_start if position == PremiumDiscountPosition.DISCOUNT else 30.0
        if direction == SignalDirection.SELL:
            return self.premium_start if position == PremiumDiscountPosition.PREMIUM else 30.0
        return 0.0

    def position_for_direction(
        self,
        direction: SignalDirection,
    ) -> PremiumDiscountPosition:
        """Return the *preferred* region for a setup direction."""
        if direction == SignalDirection.BUY:
            return PremiumDiscountPosition.DISCOUNT
        if direction == SignalDirection.SELL:
            return PremiumDiscountPosition.PREMIUM
        return PremiumDiscountPosition.EQUILIBRIUM


__all__ = ["PremiumDiscountAnalyzer"]
