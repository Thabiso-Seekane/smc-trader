"""Market structure analyzer — the public façade.

``MarketStructureAnalyzer.analyze(df)`` wires together the swing detector,
classifier, and trend analyzer so callers interact with a single entry
point.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from structure.models import MarketStructure
from structure.swing_classifier import SwingClassifier
from structure.swing_detector import SwingDetector
from structure.trend_analyzer import TrendAnalyzer


@dataclass(slots=True)
class MarketStructureAnalyzer:
    """High-level orchestrator for market-structure analysis.

    Attributes:
        lookback: Fractal lookback passed to the swing detector.
    """

    lookback: int = 2

    def analyze(self, df: pd.DataFrame) -> MarketStructure:
        """Analyze a candle DataFrame and return the market structure.

        Args:
            df: OHLCV candle DataFrame (``date``, ``open``, ``high``,
                ``low``, ``close``, ``volume``).

        Returns:
            A :class:`MarketStructure` containing the swings, classified
            points, and current/previous trend.
        """
        if df is None or df.empty:
            return MarketStructure()

        detector = SwingDetector(lookback=self.lookback)
        classifier = SwingClassifier()
        trend_analyzer = TrendAnalyzer()

        swings = detector.detect(df)
        points = classifier.classify(swings)
        current, previous = trend_analyzer.analyze(points)

        return MarketStructure(
            swings=swings,
            points=points,
            trend=current,
            previous_trend=previous,
        )


__all__ = ["MarketStructureAnalyzer"]
