"""Config-driven confluence scoring for the Strategy Engine.

The :class:`ConfluenceScorer` blends eight independent confirmation factors
into a single 0-100 score. The weights are **configuration-driven** so they
can be tuned during backtesting (Week 9) without changing source code, and
so multiple strategy profiles (conservative, balanced, aggressive) can be
created by loading different weight dictionaries.

Default weights (from the Week 7 spec):

    ==========================   ======
    Factor                         Weight
    ==========================   ======
    Higher Timeframe Bias          20
    Liquidity Sweep                15
    CHoCH                          15
    BOS                            15
    Order Block                    10
    Fair Value Gap                 10
    Premium / Discount             10
    Risk / Reward Available         5
    ==========================   ======
    Total                         100
    ==========================   ======

Suggested thresholds:

    ============   ===========
    Confidence      Tier
    ============   ===========
    90-100          EXCELLENT
    80-89           STRONG
    70-79           ACCEPTABLE
    Below 70        IGNORE
    ============   ===========
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from strategy.enums import DecisionStatus, PremiumDiscountPosition, SignalDirection


DEFAULT_WEIGHTS: dict[str, float] = {
    "higher_timeframe": 20.0,
    "liquidity_sweep": 15.0,
    "choch": 15.0,
    "bos": 15.0,
    "order_block": 10.0,
    "fair_value_gap": 10.0,
    "premium_discount": 10.0,
    "risk_reward": 5.0,
}

DEFAULT_THRESHOLDS: dict[str, float] = {
    "excellent": 90.0,
    "strong": 80.0,
    "acceptable": 70.0,
}


@dataclass(slots=True)
class ConfluenceScorer:
    """Score and rank trade setups by confluence.

    Attributes:
        weights: Mapping of factor name -> weight (defaults to spec values).
        thresholds: Mapping of tier name -> minimum confidence.
        available: Set of factor names considered "present" for a setup.
            When a factor is absent it contributes zero weight to the score.
    """

    weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    thresholds: Mapping[str, float] = field(
        default_factory=lambda: dict(DEFAULT_THRESHOLDS)
    )
    available: set[str] = field(default_factory=set)

    # --- scoring ------------------------------------------------
    def score(self, available: set[str]) -> float:
        """Compute the 0-100 weighted confluence score.

        Args:
            available: The set of confirmation factors that are present for
                a setup (e.g. ``{"higher_timeframe", "choch", "bos"}``).

        Returns:
            A 0-100 score rounded to two decimals.
        """
        self.available = set(available)
        total_weight = sum(self.weights.values())
        if total_weight <= 0:
            return 0.0
        earned = sum(
            weight for name, weight in self.weights.items() if name in self.available
        )
        score = (earned / total_weight) * 100.0
        return round(max(0.0, min(100.0, score)), 2)

    def status(self, score: float) -> DecisionStatus:
        """Map a 0-100 score to a decision tier."""
        if score >= self.thresholds["excellent"]:
            return DecisionStatus.EXCELLENT
        if score >= self.thresholds["strong"]:
            return DecisionStatus.STRONG
        if score >= self.thresholds["acceptable"]:
            return DecisionStatus.ACCEPTABLE
        return DecisionStatus.IGNORE

    def rank(self, scored: list[tuple]) -> list[tuple]:
        """Sort ``(score, setup)`` tuples by descending score."""
        return sorted(scored, key=lambda item: item[0], reverse=True)

    # --- factor helpers -----------------------------------------
    def liquidity_sweep_present(self, liquidity) -> bool:
        """Return True when the liquidity map contains a swept level."""
        if liquidity is None:
            return False
        swept = getattr(liquidity, "swept_levels", None)
        if swept is None and hasattr(liquidity, "sweeps"):
            swept = getattr(liquidity, "sweeps", None)
        return bool(swept) if swept is not None else False

    def choch_present(self, events) -> bool:
        """Return True when the events contain a CHoCH."""
        for event in _as_event_list(events):
            if getattr(event, "is_choch", False):
                return True
        return False

    def bos_present(self, events) -> bool:
        """Return True when the events contain a BOS."""
        for event in _as_event_list(events):
            if getattr(event, "is_bos", False):
                return True
        return False

    def order_block_present(self, order_blocks) -> bool:
        """Return True when there is at least one active Order Block."""
        blocks = _as_block_list(order_blocks)
        return any(getattr(b, "is_active", True) for b in blocks)

    def fvg_present(self, imbalances) -> bool:
        """Return True when there is at least one active Fair Value Gap."""
        gaps = _as_gap_list(imbalances)
        return any(getattr(g, "is_active", True) for g in gaps)

    def premium_discount_aligned(
        self,
        position: PremiumDiscountPosition,
        direction: SignalDirection,
    ) -> bool:
        """Return True when the premium/discount position matches direction."""
        if direction == SignalDirection.BUY:
            return position == PremiumDiscountPosition.DISCOUNT
        if direction == SignalDirection.SELL:
            return position == PremiumDiscountPosition.PREMIUM
        return False


def _as_event_list(events) -> list:
    """Normalize events (SmartMoneyAnalysis, EventHistory, or list) to a list."""
    if events is None:
        return []
    if isinstance(events, list):
        return events
    for attr in ("events", "history"):
        if hasattr(events, attr):
            return list(getattr(events, attr))
    return []


def _as_block_list(order_blocks) -> list:
    """Normalize Order Blocks (list, OrderBlockMap, or single) to a list."""
    if order_blocks is None:
        return []
    if isinstance(order_blocks, list):
        return order_blocks
    for attr in ("all", "bullish", "bearish"):
        if hasattr(order_blocks, attr):
            return list(getattr(order_blocks, attr))
    return []


def _as_gap_list(imbalances) -> list:
    """Normalize imbalance gaps (list or ImbalanceMap) to a list."""
    if imbalances is None:
        return []
    if isinstance(imbalances, list):
        return imbalances
    for attr in ("all", "gaps"):
        if hasattr(imbalances, attr):
            return list(getattr(imbalances, attr))
    return []


__all__ = ["ConfluenceScorer", "DEFAULT_WEIGHTS", "DEFAULT_THRESHOLDS"]
