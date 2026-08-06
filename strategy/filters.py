"""Strategy filters.

Not every setup should be traded — even a high-confluence one. Filters are
independent, enable/disable checks that gate a trade zone before it is
accepted. Keeping them independent makes it trivial to turn a rule on or
off without touching the scoring engine.

Available filters (each may be enabled/disabled):

    * ``min_confluence`` — minimum confluence score (0-100).
    * ``min_displacement`` — minimum displacement strength of the backing
      structural event.
    * ``higher_tf_alignment`` — setup must agree with the higher timeframe.
    * ``premium_discount_match`` — setup must sit in the correct
      premium/discount region.
    * ``min_risk_reward`` — minimum reward-to-risk ratio (e.g. 1.5).
    * ``max_ob_age`` — maximum age (in candles) of the anchoring Order Block.
    * ``max_ob_touches`` — maximum touch count of the Order Block.
    * ``require_liquidity_sweep`` — a liquidity sweep must be present.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from strategy.enums import PremiumDiscountPosition, SignalDirection
from strategy.models import TradeZone


@dataclass(slots=True)
class StrategyFilters:
    """Configurable, independent filters for trade-zone acceptance.

    Attributes:
        min_confluence: Minimum confluence score to pass (0 disables).
        min_displacement: Minimum displacement strength (0 disables).
        higher_tf_alignment: Require HTF agreement.
        premium_discount_match: Require correct premium/discount region.
        min_risk_reward: Minimum reward/risk ratio (0 disables).
        max_ob_age: Maximum Order Block age in candles (None disables).
        max_ob_touches: Maximum Order Block touch count (None disables).
        require_liquidity_sweep: Require a liquidity sweep present.
    """

    min_confluence: float = 70.0
    min_displacement: float = 0.0
    higher_tf_alignment: bool = False
    premium_discount_match: bool = False
    min_risk_reward: float = 0.0
    max_ob_age: int | None = None
    max_ob_touches: int | None = None
    require_liquidity_sweep: bool = False

    def passes(self, zone: TradeZone, **context) -> bool:
        """Return True when a trade zone passes all enabled filters.

        Args:
            zone: The trade zone to evaluate.
            **context: Optional extra context used by some filters, e.g.
                ``htf_bias`` (str) and ``liquidity_swept`` (bool).

        Returns:
            True when the zone passes every enabled filter.
        """
        if self.min_confluence > 0 and zone.confluence_score < self.min_confluence:
            return False

        if self.min_displacement > 0:
            event = zone.structure_event
            strength = getattr(event, "displacement_strength", 0.0) or 0.0
            if strength < self.min_displacement:
                return False

        if self.higher_tf_alignment:
            htf_bias = context.get("htf_bias", "NEUTRAL")
            if not _htf_aligns(htf_bias, zone.direction):
                return False

        if self.premium_discount_match:
            if not _premium_discount_matches(zone.premium_discount, zone.direction):
                return False

        if self.min_risk_reward > 0 and zone.risk_reward_ratio < self.min_risk_reward:
            return False

        if self.max_ob_age is not None and zone.order_block is not None:
            age = getattr(zone.order_block, "age", None)
            if age is not None and age > self.max_ob_age:
                return False

        if self.max_ob_touches is not None and zone.order_block is not None:
            touches = getattr(zone.order_block, "touch_count", 0) or 0
            if touches > self.max_ob_touches:
                return False

        if self.require_liquidity_sweep and not context.get("liquidity_swept", False):
            return False

        return True


def _htf_aligns(htf_bias: str, direction: SignalDirection) -> bool:
    """Return True when the HTF bias agrees with the setup direction."""
    upper = (htf_bias or "NEUTRAL").upper()
    if direction == SignalDirection.BUY:
        return upper == "BULLISH"
    if direction == SignalDirection.SELL:
        return upper == "BEARISH"
    return False


def _premium_discount_matches(
    position: PremiumDiscountPosition, direction: SignalDirection
) -> bool:
    """Return True when the premium/discount position matches the direction."""
    if direction == SignalDirection.BUY:
        return position == PremiumDiscountPosition.DISCOUNT
    if direction == SignalDirection.SELL:
        return position == PremiumDiscountPosition.PREMIUM
    return False


__all__ = ["StrategyFilters"]
