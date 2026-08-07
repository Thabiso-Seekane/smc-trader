"""Take-profit placement for the Week 8 Risk Engine.

This module answers: *"Where should my take-profit go?"*

It derives the profit target from an R-multiple, a structural level, or a
fixed distance. The execution layer reads the target from the plan and
never computes it again.
"""

from __future__ import annotations

from dataclasses import dataclass

from risk.enums import TakeProfitMode


@dataclass(slots=True)
class TakeProfitPlacer:
    """Place a take-profit target for a trade plan.

    Attributes:
        mode: How the target is derived.
        rr_multiple: R-multiple used when mode is RR_MULTIPLE (e.g. 2.0 = 2R).
        fixed_distance: Fixed price distance used when mode is FIXED_PIPS.
    """

    mode: TakeProfitMode = TakeProfitMode.RR_MULTIPLE
    rr_multiple: float = 2.0
    fixed_distance: float = 0.0

    def place(
        self,
        *,
        direction: str,
        entry: float,
        stop: float,
        structural_target: float | None = None,
    ) -> float:
        """Return the take-profit price for a trade.

        Args:
            direction: "BUY" or "SELL".
            entry: The entry price.
            stop: The stop-loss price.
            structural_target: A structural target price (swing / prior high-low).

        Returns:
            The take-profit price.
        """
        risk = abs(entry - stop)
        if risk <= 0:
            return 0.0

        if self.mode == TakeProfitMode.RR_MULTIPLE and self.rr_multiple > 0:
            return self._on_side(direction, entry, risk * self.rr_multiple)

        if self.mode == TakeProfitMode.FIXED_PIPS and self.fixed_distance > 0:
            return self._on_side(direction, entry, self.fixed_distance)

        # STRUCTURAL (default)
        if structural_target is None or structural_target <= 0:
            return 0.0
        return self._ensure_side(direction, entry, structural_target)

    def _on_side(self, direction: str, entry: float, distance: float) -> float:
        """Place the target on the correct side of entry."""
        if direction.upper() == "BUY":
            return entry + distance
        return entry - distance

    def _ensure_side(self, direction: str, entry: float, target: float) -> float:
        """Guarantee the target is on the correct side of the entry."""
        if direction.upper() == "BUY":
            return target if target > entry else entry + 0.0001
        return target if target < entry else entry - 0.0001


__all__ = ["TakeProfitPlacer"]
