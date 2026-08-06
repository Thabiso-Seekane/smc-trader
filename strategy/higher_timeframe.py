"""Higher Timeframe (HTF) bias analyzer.

One of the biggest mistakes retail automation makes is trading *against* the
higher timeframe. This module analyzes the higher-timeframe direction and
returns a bias the strategy uses to either align or reject a setup.

The analyzer accepts a higher-timeframe ``MarketStructure`` (or a simple
bias string) and returns:

* the HTF **bias** (BULLISH / BEARISH / NEUTRAL),
* a 0-100 **alignment score** for a given setup direction (a setup that
  agrees with the HTF scores full marks; a counter-HTF setup scores low).
"""

from __future__ import annotations

from dataclasses import dataclass

from strategy.enums import SignalDirection


@dataclass(slots=True)
class HigherTimeframeAnalyzer:
    """Analyze the higher-timeframe bias and its alignment with a setup.

    Attributes:
        bullish_text: Substrings that indicate a bullish HTF.
        bearish_text: Substrings that indicate a bearish HTF.
    """

    bullish_text: tuple[str, ...] = ("BULLISH", "BULL", "UP", "LONG")
    bearish_text: tuple[str, ...] = ("BEARISH", "BEAR", "DOWN", "SHORT")

    def bias_from_structure(self, structure) -> str:
        """Derive the HTF bias from a ``MarketStructure`` object.

        The structure is expected to expose a ``trend`` attribute (or a
        ``latest_direction`` / ``trend_direction``) whose value is a string
        like ``"BULLISH"`` or ``"BEARISH"``. If no clear signal is found,
        ``NEUTRAL`` is returned.

        Args:
            structure: A higher-timeframe market structure object.

        Returns:
            ``"BULLISH"``, ``"BEARISH"``, or ``"NEUTRAL"``.
        """
        text = ""
        for attr in ("trend", "trend_direction", "latest_direction", "bias"):
            value = getattr(structure, attr, None)
            if value is not None:
                text += " " + str(value)
        label = getattr(structure, "trend_label", None)
        if label is not None:
            text += " " + str(label)
        return self.bias_from_text(text)

    def bias_from_text(self, text: str) -> str:
        """Classify raw text into a bullish / bearish / neutral bias."""
        upper = (text or "").upper()
        if any(t in upper for t in self.bullish_text):
            return "BULLISH"
        if any(t in upper for t in self.bearish_text):
            return "BEARISH"
        return "NEUTRAL"

    def score(self, bias: str, direction: SignalDirection) -> float:
        """Return a 0-100 alignment score for a setup direction.

        A setup that agrees with the HTF bias scores 100; a neutral bias
        scores 50; a setup that fights the HTF scores 0.

        Args:
            bias: The HTF bias (``"BULLISH"`` / ``"BEARISH"`` / ``"NEUTRAL"``).
            direction: The setup direction.

        Returns:
            0-100 alignment score.
        """
        if bias == "NEUTRAL":
            return 50.0
        if direction == SignalDirection.BUY:
            return 100.0 if bias == "BULLISH" else 0.0
        if direction == SignalDirection.SELL:
            return 100.0 if bias == "BEARISH" else 0.0
        return 0.0

    def aligns(self, bias: str, direction: SignalDirection) -> bool:
        """Return True when a setup direction agrees with the HTF bias."""
        return self.score(bias, direction) >= 100.0


__all__ = ["HigherTimeframeAnalyzer"]
