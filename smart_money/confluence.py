"""Confluence scoring for Trade Zones.

A Trade Zone combines multiple independent confirmation factors. The
``ConfluenceScorer`` blends them into a single 0-100 score so the strategy
layer can answer "where is the highest-probability trading zone?".

Suggested weighting:

    =============================   ======
    Factor                            Weight
    =============================   ======
    Order Block Strength              30
    Fair Value Gap Presence           20
    Liquidity Interaction             20
    Structural Event Context          15
    Higher-Timeframe Alignment        15
    =============================   ======
    Total                            100
    =============================   ======

A score of 0-39 is WEAK, 40-69 is MODERATE, and 70+ is STRONG.
"""

from __future__ import annotations

from dataclasses import dataclass

from smart_money.enums import ConfluenceLevel, FreshnessLevel
from smart_money.trade_zone_models import TradeZone


@dataclass(slots=True)
class ConfluenceScorer:
    """Score and rank Trade Zones by confluence.

    Attributes:
        order_block_weight: Weight (0-100 split) for the Order Block anchor.
        fvg_weight: Weight for Fair Value Gap presence.
        liquidity_weight: Weight for liquidity interaction.
        structure_weight: Weight for structural event context.
        timeframe_weight: Weight for higher-timeframe alignment.
    """

    order_block_weight: float = 30.0
    fvg_weight: float = 20.0
    liquidity_weight: float = 20.0
    structure_weight: float = 15.0
    timeframe_weight: float = 15.0

    def score(self, zone: TradeZone) -> TradeZone:
        """Compute the 0-100 confluence score for a single zone.

        Args:
            zone: The Trade Zone to score.

        Returns:
            The same zone, mutated with ``confluence_score`` and
            ``confluence_level`` set.
        """
        zone.confluence_score = self._compute(zone)
        zone.confluence_level = self._level(zone.confluence_score)
        return zone

    def rank(self, zones: list[TradeZone]) -> list[TradeZone]:
        """Score each zone and return them sorted by confluence (descending).

        Args:
            zones: The Trade Zones to score.

        Returns:
            The zones, mutated with scores, sorted by descending confluence.
        """
        for zone in zones:
            self.score(zone)
        return sorted(zones, key=lambda z: z.confluence_score, reverse=True)

    def _compute(self, zone: TradeZone) -> float:
        """Compute the weighted 0-100 confluence score for a zone."""
        scores = {
            "ob": self._order_block_factor(zone),
            "fvg": self._fvg_factor(zone),
            "liquidity": self._liquidity_factor(zone),
            "structure": self._structure_factor(zone),
            "timeframe": self._timeframe_factor(zone),
        }
        weights = {
            "ob": self.order_block_weight,
            "fvg": self.fvg_weight,
            "liquidity": self.liquidity_weight,
            "structure": self.structure_weight,
            "timeframe": self.timeframe_weight,
        }
        total = sum(weights.values())
        if total <= 0:
            return 0.0
        score = sum(scores[k] * weights[k] for k in weights) / total
        return round(max(0.0, min(100.0, score)), 2)

    def _order_block_factor(self, zone: TradeZone) -> float:
        """0-100 from the anchoring Order Block's strength and freshness."""
        ob = zone.order_block
        if ob is None:
            return 0.0
        strength = getattr(ob, "strength", 0.0) or 0.0
        # Freshness boosts; mitigated/consumed zones score lower.
        freshness = getattr(ob, "freshness", None)
        if freshness == FreshnessLevel.FRESH:
            return min(100.0, strength)
        if freshness == FreshnessLevel.TOUCHED_ONCE:
            return min(100.0, strength) * 0.8
        if freshness == FreshnessLevel.TOUCHED_TWICE:
            return min(100.0, strength) * 0.6
        return min(100.0, strength) * 0.4

    def _fvg_factor(self, zone: TradeZone) -> float:
        """0-100 from Fair Value Gap presence and strength."""
        if not zone.fair_value_gaps:
            return 0.0
        strengths = [g.strength for g in zone.fair_value_gaps if g.strength > 0]
        if strengths:
            return min(100.0, max(strengths))
        return 70.0  # FVG present but strength not yet computed (Week 6).

    def _liquidity_factor(self, zone: TradeZone) -> float:
        """0-100 from nearby liquidity interaction."""
        if not zone.liquidity_levels:
            return 50.0  # neutral — a zone without liquidity still has merit.
        best = 50.0
        for level in zone.liquidity_levels:
            strength = getattr(level, "strength", 0.0) or 0.0
            base = 60.0 if getattr(level, "is_external", False) else 80.0
            best = max(best, min(100.0, base + strength * 0.5))
        return best

    def _structure_factor(self, zone: TradeZone) -> float:
        """0-100 from structural event context (CHoCH stronger than BOS)."""
        if not zone.events:
            return 50.0  # neutral
        best = 50.0
        for event in zone.events:
            if getattr(event, "is_choch", False):
                best = max(best, 100.0)
            elif getattr(event, "is_bos", False):
                best = max(best, 70.0)
            elif getattr(event, "is_bullish", False):
                best = max(best, 60.0)
        return best

    def _timeframe_factor(self, zone: TradeZone) -> float:
        """0-100 from the timeframe label (higher timeframes are stronger)."""
        tf = (zone.timeframe or "").upper()
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

    def _level(self, score: float) -> ConfluenceLevel:
        """Map a 0-100 confluence score to a quality tier."""
        if score <= 0:
            return ConfluenceLevel.NONE
        if score < 40:
            return ConfluenceLevel.WEAK
        if score < 70:
            return ConfluenceLevel.MODERATE
        return ConfluenceLevel.STRONG


__all__ = ["ConfluenceScorer"]
