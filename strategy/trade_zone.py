"""Trade Zone builder.

The :class:`TradeZoneBuilder` assembles a complete :class:`TradeZone`
setup from the upstream detection maps. It extracts the anchoring Order
Block, the overlapping Fair Value Gap, the interacting liquidity level, and
the confirming structural event, then computes entry/stop/target geometry
and the premium/discount position.

The builder is intentionally direction-agnostic: it produces both a bullish
and a bearish setup for each candidate so the ConfluenceEngine can decide
which one is stronger.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from strategy.enums import PremiumDiscountPosition, SignalDirection
from strategy.models import TradeZone
from strategy.premium_discount import PremiumDiscountAnalyzer

from liquidity.models import LiquidityMap
from smart_money.models import SmartMoneyAnalysis
from smart_money.order_block_models import OrderBlockMap
from smart_money.imbalance import ImbalanceMap
from structure.models import MarketStructure


@dataclass(slots=True)
class TradeZoneBuilder:
    """Build directional setups from the upstream detection maps.

    Attributes:
        premium_discount: The premium/discount analyzer used to label the
            zone's position.
        timeframe: Label attached to built zones.
        risk_multiplier: How many R's from entry to stop-loss (0.5R default).
        reward_ratio: Reward-to-risk ratio applied to the target (2R default).
    """

    premium_discount: PremiumDiscountAnalyzer = field(
        default_factory=PremiumDiscountAnalyzer
    )
    timeframe: str = field(default="", kw_only=True)
    risk_multiplier: float = 0.5
    reward_ratio: float = 2.0

    def build(
        self,
        *,
        direction: SignalDirection,
        structure: MarketStructure,
        liquidity: LiquidityMap,
        events,
        order_blocks: OrderBlockMap,
        imbalances: ImbalanceMap,
        entry_price: float,
        reference_price: float | None = None,
    ) -> TradeZone:
        """Build a single directional trade zone.

        Args:
            direction: Buy or sell bias.
            structure: The market structure (used for premium/discount).
            liquidity: The liquidity map.
            events: The structural events.
            order_blocks: The order block map.
            imbalances: The imbalance (FVG) map.
            entry_price: The ideal entry price.
            reference_price: Optional last-close / current price used to
                locate the nearest anchor. When omitted, ``entry_price`` is
                used.

        Returns:
            A :class:`TradeZone` with geometry and attached confirms.
        """
        ref = reference_price if reference_price is not None else entry_price

        order_block = self._best_block(order_blocks, direction)
        fair_value_gap = self._best_gap(imbalances, direction)
        liquidity_level = self._best_liquidity(liquidity, direction, ref)
        structure_event = self._best_event(events, direction)

        high, low = self._dealing_range(structure)
        stop_loss, target = self._geometry(
            direction, entry_price, high, low, order_block, fair_value_gap
        )
        position = self.premium_discount.analyze(entry_price, high, low)

        return TradeZone(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            order_block=order_block,
            fair_value_gap=fair_value_gap,
            liquidity=liquidity_level,
            structure_event=structure_event,
            premium_discount=position,
            timeframe=self.timeframe,
        )

    # --- selecting anchors -------------------------------------
    def _best_block(self, order_blocks, direction: SignalDirection):
        """Return the highest-strength active Order Block of a direction."""
        blocks = _as_block_list(order_blocks)
        candidates = [
            b
            for b in blocks
            if getattr(b, "is_active", True)
            and _matches_direction(b, direction)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda b: getattr(b, "strength", 0.0) or 0.0)

    def _best_gap(self, imbalances, direction: SignalDirection):
        """Return the strongest active FVG of a direction."""
        gaps = _as_gap_list(imbalances)
        candidates = [
            g
            for g in gaps
            if getattr(g, "is_active", True) and _matches_direction(g, direction)
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda g: getattr(g, "strength", 0.0) or 0.0,
        )

    def _best_liquidity(self, liquidity, direction: SignalDirection, ref: float):
        """Return the nearest unswept liquidity level of a direction."""
        levels = _as_level_list(liquidity)
        candidates = [
            level
            for level in levels
            if not getattr(level, "swept", True) and _matches_direction(level, direction)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda level: abs(float(level.price) - ref))

    def _best_event(self, events, direction: SignalDirection):
        """Return the most recent structural event of a direction."""
        event_list = _as_event_list(events)
        candidates = [
            e for e in event_list if _matches_direction(e, direction)
        ]
        if not candidates:
            return None
        return candidates[-1]

    # --- geometry ----------------------------------------------
    def _dealing_range(self, structure):
        """Return (swing_high, swing_low) from the latest structure swings."""
        swings = getattr(structure, "swings", None) or []
        highs = [s.price for s in swings if getattr(s, "is_high", False)]
        lows = [s.price for s in swings if not getattr(s, "is_high", False)]
        high = max(highs) if highs else 0.0
        low = min(lows) if lows else 0.0
        return high, low

    def _geometry(
        self,
        direction: SignalDirection,
        entry: float,
        high: float,
        low: float,
        order_block,
        fair_value_gap,
    ):
        """Compute stop-loss and target from the anchor geometry."""
        # Prefer the order block edge as the stop reference.
        anchor_high = getattr(order_block, "high", None) or (
            getattr(fair_value_gap, "high", None) or 0.0
        )
        anchor_low = getattr(order_block, "low", None) or (
            getattr(fair_value_gap, "low", None) or 0.0
        )

        if direction == SignalDirection.BUY:
            stop_ref = anchor_low if anchor_low else low
            stop = entry - abs(entry - stop_ref) if stop_ref else entry - (high - low) * 0.5
            risk = abs(entry - stop) or 1.0
            target = entry + risk * self.reward_ratio
        elif direction == SignalDirection.SELL:
            stop_ref = anchor_high if anchor_high else high
            stop = entry + abs(stop_ref - entry) if stop_ref else entry + (high - low) * 0.5
            risk = abs(stop - entry) or 1.0
            target = entry - risk * self.reward_ratio
        else:
            return entry, entry

        return float(stop), float(target)


def _matches_direction(obj, direction: SignalDirection) -> bool:
    """Return True when an anchor's direction matches the setup direction."""
    # Liquidity levels expose buy-side / sell-side helpers.
    is_buy_side = getattr(obj, "is_buy_side", None)
    if is_buy_side is not None:
        matches = bool(is_buy_side) == (direction == SignalDirection.BUY)
        return matches

    is_bullish = getattr(obj, "is_bullish", None)
    is_bearish = getattr(obj, "is_bearish", None)
    if is_bullish is not None:
        return bool(is_bullish) == (direction == SignalDirection.BUY)
    if is_bearish is not None:
        return bool(is_bearish) == (direction == SignalDirection.SELL)
    # Fall back to a `direction` attribute.
    dir_value = getattr(obj, "direction", None)
    if dir_value is None:
        return False
    text = str(dir_value).upper()
    if direction == SignalDirection.BUY:
        return "BULL" in text
    if direction == SignalDirection.SELL:
        return "BEAR" in text
    return False


def _as_block_list(order_blocks) -> list:
    if order_blocks is None:
        return []
    if isinstance(order_blocks, list):
        return order_blocks
    for attr in ("all", "bullish", "bearish"):
        if hasattr(order_blocks, attr):
            return list(getattr(order_blocks, attr))
    return []


def _as_gap_list(imbalances) -> list:
    if imbalances is None:
        return []
    if isinstance(imbalances, list):
        return imbalances
    for attr in ("all", "gaps"):
        if hasattr(imbalances, attr):
            return list(getattr(imbalances, attr))
    return []


def _as_level_list(liquidity) -> list:
    if liquidity is None:
        return []
    if isinstance(liquidity, list):
        return liquidity
    for attr in ("levels", "active_levels"):
        if hasattr(liquidity, attr):
            return list(getattr(liquidity, attr))
    return []


def _as_event_list(events) -> list:
    if events is None:
        return []
    if isinstance(events, list):
        return events
    for attr in ("events", "history"):
        if hasattr(events, attr):
            return list(getattr(events, attr))
    return []


__all__ = ["TradeZoneBuilder"]
