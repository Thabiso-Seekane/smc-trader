"""Ranking for Order Block zones.

Every Order Block receives a 0-100 composite score. The weightings are
tuned so that fresh, high-displacement zones in strong structural context
with liquidity interaction score highest.

Suggested weighting:

    =========================   ======
    Factor                       Weight
    =========================   ======
    Displacement Strength        25
    Freshness                    20
    Structural Context (CHoCH/BOS) 20
    Liquidity Interaction        15
    Timeframe                    10
    Candle Quality               10
    =========================   ======
    Total                        100
    =========================   ======
"""

from __future__ import annotations

from dataclasses import dataclass

from smart_money.enums import (
    Direction,
    FreshnessLevel,
    OrderBlockQuality,
    OrderBlockType,
)
from smart_money.order_block_models import OrderBlock


@dataclass(slots=True)
class OrderBlockRanker:
    """Score and order Order Block zones.

    Attributes:
        displacement_weight: Weight (0-100 split) for displacement strength.
        freshness_weight: Weight for freshness.
        structure_weight: Weight for structural context (CHoCH vs BOS).
        liquidity_weight: Weight for liquidity interaction.
        timeframe_weight: Weight for the timeframe.
        candle_weight: Weight for candle quality.
    """

    displacement_weight: float = 25.0
    freshness_weight: float = 20.0
    structure_weight: float = 20.0
    liquidity_weight: float = 15.0
    timeframe_weight: float = 10.0
    candle_weight: float = 10.0

    def rank(
        self,
        blocks: list[OrderBlock],
        structure_events=None,
        liquidity_map=None,
    ) -> list[OrderBlock]:
        """Score each block and return them sorted by strength (descending).

        Args:
            blocks: The Order Block zones to rank.
            structure_events: Optional Week 4 events for structural-context
                scoring (CHoCH stronger than BOS).
            liquidity_map: Optional Week 3 liquidity map for liquidity
                interaction scoring.

        Returns:
            The blocks, mutated with ``strength`` and ``quality``, sorted by
            descending strength.
        """
        for block in blocks:
            block.strength = self._score(
                block,
                structure_events=structure_events or [],
                liquidity_map=liquidity_map,
            )
            block.quality = self._quality(block.strength)
        return sorted(blocks, key=lambda b: b.strength, reverse=True)

    def _score(self, block: OrderBlock, structure_events, liquidity_map) -> float:
        """Compute the 0-100 composite score for a single block."""
        scores = {
            "displacement": self._displacement_factor(block),
            "freshness": self._freshness_factor(block),
            "structure": self._structure_factor(block, structure_events),
            "liquidity": self._liquidity_factor(block, liquidity_map),
            "timeframe": self._timeframe_factor(block),
            "candle": self._candle_factor(block),
        }
        weights = {
            "displacement": self.displacement_weight,
            "freshness": self.freshness_weight,
            "structure": self.structure_weight,
            "liquidity": self.liquidity_weight,
            "timeframe": self.timeframe_weight,
            "candle": self.candle_weight,
        }
        total = sum(weights.values())
        if total <= 0:
            return 0.0
        score = sum(scores[k] * weights[k] for k in weights) / total
        return round(max(0.0, min(100.0, score)), 2)

    def _displacement_factor(self, block: OrderBlock) -> float:
        """0-100 from displacement strength (clamped)."""
        return max(0.0, min(100.0, block.displacement_score))

    def _freshness_factor(self, block: OrderBlock) -> float:
        """0-100 from freshness tier.

        Fresh=100, touched once=70, touched twice=35, mitigated=10.
        """
        mapping = {
            FreshnessLevel.FRESH: 100.0,
            FreshnessLevel.TOUCHED_ONCE: 70.0,
            FreshnessLevel.TOUCHED_TWICE: 35.0,
            FreshnessLevel.MITIGATED: 10.0,
        }
        return mapping.get(block.freshness, 50.0)

    def _structure_factor(self, block: OrderBlock, structure_events) -> float:
        """0-100 from the creating event's structural context.

        CHoCH events are stronger reversal signals than BOS continuations.
        """
        direction = block.created_from_event
        for event in structure_events:
            # Match the event to this block by displacement + direction.
            if abs(event.displacement_strength - block.displacement_score) < 1e-9:
                if event.is_choch:
                    return 100.0
                if event.is_bos:
                    return 70.0
        # Fallback: 50 if no matching event is found.
        return 50.0

    def _liquidity_factor(self, block: OrderBlock, liquidity_map) -> float:
        """0-100 from liquidity interaction.

        A zone near a strong / external liquidity pool scores higher.
        """
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
            if block.low <= price <= block.high:
                strength = getattr(level, "strength", 0.0) or 0.0
                external = bool(getattr(level, "is_external", False))
                base = 60.0 if external else 80.0
                best = max(best, min(100.0, base + strength))
        return best

    def _timeframe_factor(self, block: OrderBlock) -> float:
        """0-100 from the timeframe label (higher timeframes are stronger)."""
        tf = (block.timeframe or "").upper()
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

    def _candle_factor(self, block: OrderBlock) -> float:
        """0-100 from candle quality (body-to-range ratio of the origin)."""
        rng = block.range
        if rng <= 0:
            return 0.0
        # Approximate body from displacement geometry; higher displacement
        # implies a stronger body on the originating move.
        body_ratio = min(1.0, block.displacement_score / 100.0)
        return round(body_ratio * 100.0, 2)

    def _quality(self, strength: float) -> OrderBlockQuality:
        """Map a 0-100 strength to a quality label."""
        if strength <= 0:
            return OrderBlockQuality.NONE
        if strength < 40:
            return OrderBlockQuality.WEAK
        if strength < 70:
            return OrderBlockQuality.MODERATE
        return OrderBlockQuality.STRONG


__all__ = ["OrderBlockRanker"]
