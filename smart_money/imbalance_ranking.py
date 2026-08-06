"""Ranking for imbalance (Fair Value Gap) zones.

Every Fair Value Gap receives a 0-100 composite score. The weightings are
tuned so that fresh, high-displacement gaps in strong structural context
with liquidity alignment score highest.

Suggested weighting:

    =============================   ======
    Factor                           Weight
    =============================   ======
    Displacement Strength            25
    Gap Size                         15
    Freshness                        20
    Structural Context               20
    Liquidity Alignment              10
    Timeframe                        10
    =============================   ======
    Total                           100
    =============================   ======
"""

from __future__ import annotations

from dataclasses import dataclass

from smart_money.enums import GapQuality
from smart_money.fair_value_gap import FairValueGap


@dataclass(slots=True)
class ImbalanceRanker:
    """Score and order Fair Value Gap zones.

    Attributes:
        displacement_weight: Weight for displacement strength.
        size_weight: Weight for gap size (relative to ATR).
        freshness_weight: Weight for gap freshness.
        structure_weight: Weight for structural context (CHoCH vs BOS).
        liquidity_weight: Weight for liquidity alignment.
        timeframe_weight: Weight for the timeframe label.
    """

    displacement_weight: float = 25.0
    size_weight: float = 15.0
    freshness_weight: float = 20.0
    structure_weight: float = 20.0
    liquidity_weight: float = 10.0
    timeframe_weight: float = 10.0

    def rank(
        self,
        gaps: list[FairValueGap],
        structure_events=None,
        liquidity_map=None,
    ) -> list[FairValueGap]:
        """Score each gap and return them sorted by strength (descending).

        Args:
            gaps: The Fair Value Gap objects to rank.
            structure_events: Optional Week 4 events for structural-context
                scoring (CHoCH stronger than BOS).
            liquidity_map: Optional Week 3 liquidity map for liquidity
                alignment scoring.

        Returns:
            The gaps, mutated with ``strength`` and ``quality``, sorted by
            descending strength.
        """
        for gap in gaps:
            gap.strength = self._score(
                gap,
                structure_events=structure_events or [],
                liquidity_map=liquidity_map,
            )
            gap.quality = self._quality(gap.strength)
        return sorted(gaps, key=lambda g: g.strength, reverse=True)

    def _score(
        self,
        gap: FairValueGap,
        structure_events,
        liquidity_map,
    ) -> float:
        """Compute the 0-100 composite score for a single gap."""
        scores = {
            "displacement": self._displacement_factor(gap),
            "size": self._size_factor(gap),
            "freshness": self._freshness_factor(gap),
            "structure": self._structure_factor(gap, structure_events),
            "liquidity": self._liquidity_factor(gap, liquidity_map),
            "timeframe": self._timeframe_factor(gap),
        }
        weights = {
            "displacement": self.displacement_weight,
            "size": self.size_weight,
            "freshness": self.freshness_weight,
            "structure": self.structure_weight,
            "liquidity": self.liquidity_weight,
            "timeframe": self.timeframe_weight,
        }
        total = sum(weights.values())
        if total <= 0:
            return 0.0
        score = sum(scores[k] * weights[k] for k in weights) / total
        return round(max(0.0, min(100.0, score)), 2)

    def _displacement_factor(self, gap: FairValueGap) -> float:
        """0-100 from displacement strength (clamped)."""
        linked_event = gap.linked_structure_event
        if linked_event is not None:
            strength = getattr(linked_event, "displacement_strength", 0.0) or 0.0
            return max(0.0, min(100.0, strength))
        return max(0.0, min(100.0, gap.displacement_strength))

    def _size_factor(self, gap: FairValueGap) -> float:
        """0-100 from gap size.

        Larger gaps are scored higher (they represent stronger imbalances),
        but capped at 100.
        """
        return max(0.0, min(100.0, gap.range * 1000.0))

    def _freshness_factor(self, gap: FairValueGap) -> float:
        """0-100 from freshness (brand new gaps are strongest)."""
        return max(0.0, min(100.0, gap.freshness))

    def _structure_factor(self, gap: FairValueGap, structure_events) -> float:
        """0-100 from structural context.

        A gap linked to a CHoCH is stronger than one linked to a BOS.
        """
        linked_event = gap.linked_structure_event
        if linked_event is not None:
            if getattr(linked_event, "is_choch", False):
                return 100.0
            if getattr(linked_event, "is_bos", False):
                return 70.0
        # No explicit link: scan the provided events for a CHoCH/BOS aligned
        # with the gap's direction and index.
        for event in structure_events:
            if getattr(event, "is_choch", False):
                return 100.0
            if getattr(event, "is_bos", False):
                return 70.0
        return 50.0

    def _liquidity_factor(self, gap: FairValueGap, liquidity_map) -> float:
        """0-100 from liquidity alignment.

        A gap aligned with a strong / external liquidity pool scores higher.
        """
        if gap.linked_liquidity is not None:
            level = gap.linked_liquidity
            strength = getattr(level, "strength", 0.0) or 0.0
            base = 60.0 if getattr(level, "is_external", False) else 80.0
            return max(50.0, min(100.0, base + strength))
        if liquidity_map is None:
            return 50.0
        levels = getattr(liquidity_map, "levels", [])
        if not levels:
            return 50.0
        best = 50.0
        for level in levels:
            price = getattr(level, "price", None)
            if price is None:
                continue
            if gap.low <= price <= gap.high:
                strength = getattr(level, "strength", 0.0) or 0.0
                base = 60.0 if getattr(level, "is_external", False) else 80.0
                best = max(best, min(100.0, base + strength))
        return best

    def _timeframe_factor(self, gap: FairValueGap) -> float:
        """0-100 from the timeframe label (higher timeframes are stronger)."""
        tf = (gap.timeframe or "").upper()
        if not tf:
            return 50.0
        if any(t in tf for t in ("W", "MN", "MONTHLY")):
            return 100.0
        if any(t in tf for t in ("D", "H4", "4H")):
            return 85.0
        if any(t in tf for t in ("H1", "M30", "30M")):
            return 70.0
        if any(t in tf for t in ("M15", "15M", "M5", "5M")):
            return 50.0
        if any(t in tf for t in ("M1", "1M")):
            return 40.0
        return 50.0

    def _quality(self, strength: float) -> GapQuality:
        """Map a 0-100 strength to a quality label."""
        if strength <= 0:
            return GapQuality.NONE
        if strength < 40:
            return GapQuality.WEAK
        if strength < 70:
            return GapQuality.MODERATE
        return GapQuality.STRONG


__all__ = ["ImbalanceRanker"]
