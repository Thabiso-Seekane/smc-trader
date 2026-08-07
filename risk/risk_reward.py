"""Risk/reward analysis for the Week 8 Risk Engine.

This module answers: *"Does this trade meet the minimum R:R?"*

It computes the reward-to-risk ratio from the plan's entry/stop/target and
validates it against a minimum threshold.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RiskRewardAnalyzer:
    """Analyze and validate the reward-to-risk ratio of a trade.

    Attributes:
        min_rr: Minimum acceptable reward-to-risk ratio (e.g. 2.0).
    """

    min_rr: float = 2.0

    def analyze(
        self,
        *,
        entry: float,
        stop: float,
        target: float,
    ) -> float:
        """Return the reward-to-risk ratio of a setup.

        Returns 0.0 when risk distance is zero or the geometry is invalid.
        """
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if risk <= 0:
            return 0.0
        return reward / risk

    def meets_minimum(
        self,
        *,
        entry: float,
        stop: float,
        target: float,
        min_rr: float | None = None,
    ) -> bool:
        """Return True when the setup's R:R meets (or exceeds) the minimum."""
        ratio = self.analyze(entry=entry, stop=stop, target=target)
        threshold = self.min_rr if min_rr is None else min_rr
        return ratio >= threshold

    def quality(self, ratio: float) -> str:
        """Classify an R:R ratio into a human-readable tier."""
        if ratio <= 0:
            return "NONE"
        if ratio >= 3.0:
            return "EXCELLENT"
        if ratio >= 2.0:
            return "GOOD"
        if ratio >= 1.0:
            return "FAIR"
        return "POOR"


__all__ = ["RiskRewardAnalyzer"]
