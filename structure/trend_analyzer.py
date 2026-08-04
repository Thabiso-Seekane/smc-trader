"""Trend analysis.

Consumes classified swings and derives the current trend as well as the
previous trend. Bullish sequences (HH/HL) produce a bullish trend,
bearish sequences (LL/LH) produce a bearish trend, and mixed or
insufficient sequences resolve to a transition or range state.
"""

from __future__ import annotations

from dataclasses import dataclass

from structure.enums import StructureLabel, Trend
from structure.models import StructurePoint


@dataclass(slots=True)
class TrendAnalyzer:
    """Analyzes the trend from classified swing points."""

    def analyze(self, points: list[StructurePoint]) -> tuple[Trend, Trend]:
        """Return ``(current_trend, previous_trend)``.

        Args:
            points: Classified structure points, sorted by index.

        Returns:
            A tuple of the current and previous trend states.
        """
        if not points:
            return Trend.RANGE, Trend.RANGE

        labels = [p.label for p in points]

        # Split the sequence into HH/HL (bullish) and LL/LH (bearish).
        bullish = {StructureLabel.HH, StructureLabel.HL}
        bearish = {StructureLabel.LL, StructureLabel.LH}

        bullish_count = sum(1 for label in labels if label in bullish)
        bearish_count = sum(1 for label in labels if label in bearish)

        # Determine the current trend from the most recent swing.
        if labels:
            last = labels[-1]
            if last in bullish:
                current = Trend.BULLISH
            elif last in bearish:
                current = Trend.BEARISH
            else:
                current = Trend.RANGE
        else:
            current = Trend.RANGE

        # Determine the previous trend from the second-to-last swing.
        if len(labels) >= 2:
            prev = labels[-2]
            if prev in bullish:
                previous = Trend.BULLISH
            elif prev in bearish:
                previous = Trend.BEARISH
            else:
                previous = Trend.RANGE
        else:
            previous = Trend.RANGE

        # Mixed structure signals a transition.
        if bullish_count and bearish_count:
            current = Trend.TRANSITION
            if previous == Trend.BULLISH:
                previous = Trend.BULLISH
            elif previous == Trend.BEARISH:
                previous = Trend.BEARISH

        return current, previous


__all__ = ["TrendAnalyzer"]
