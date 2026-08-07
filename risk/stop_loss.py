"""Stop-loss placement for the Week 8 Risk Engine.

This module answers: *"Where should my stop-loss go?"*

It derives a protective stop from the setup's structural stop, an ATR
buffer, or a fixed distance. The execution layer reads the stop from the
plan and never computes it again.
"""

from __future__ import annotations

from dataclasses import dataclass

from risk.enums import StopLossMode


@dataclass(slots=True)
class StopLossPlacer:
    """Place a protective stop-loss for a trade plan.

    Attributes:
        mode: How the stop is derived.
        atr_multiplier: ATR multiple used when mode is ATR.
        fixed_distance: Fixed price distance used when mode is FIXED_PIPS.
        buffer_pct: Optional extra buffer added to the structural stop.
    """

    mode: StopLossMode = StopLossMode.STRUCTURAL
    atr_multiplier: float = 1.5
    fixed_distance: float = 0.0
    buffer_pct: float = 0.0

    def place(
        self,
        *,
        direction: str,
        entry: float,
        structural_stop: float | None = None,
        atr: float = 0.0,
    ) -> float:
        """Return the stop-loss price for a trade.

        Args:
            direction: "BUY" or "SELL".
            entry: The entry price.
            structural_stop: A structural stop price (swing / OB edge).
            atr: The current ATR value (used when mode is ATR).

        Returns:
            The stop-loss price.
        """
        if self.mode == StopLossMode.ATR and atr > 0:
            distance = atr * self.atr_multiplier
            return self._on_side(direction, entry, distance)

        if self.mode == StopLossMode.FIXED_PIPS and self.fixed_distance > 0:
            return self._on_side(direction, entry, self.fixed_distance)

        # STRUCTURAL (default)
        if structural_stop is None or structural_stop <= 0:
            return 0.0
        stop = self._apply_buffer(direction, structural_stop, entry)
        return self._ensure_side(direction, entry, stop)

    def _on_side(self, direction: str, entry: float, distance: float) -> float:
        """Place the stop on the correct side of entry."""
        if direction.upper() == "BUY":
            return entry - distance
        return entry + distance

    def _apply_buffer(self, direction: str, stop: float, entry: float) -> float:
        """Nudge a structural stop further out by a buffer percentage."""
        if self.buffer_pct <= 0:
            return stop
        distance = abs(entry - stop)
        buffer = distance * (self.buffer_pct / 100.0)
        if direction.upper() == "BUY":
            return stop - buffer
        return stop + buffer

    def _ensure_side(self, direction: str, entry: float, stop: float) -> float:
        """Guarantee the stop is on the correct side of the entry."""
        if direction.upper() == "BUY":
            return stop if stop < entry else entry - 0.0001
        return stop if stop > entry else entry + 0.0001


__all__ = ["StopLossPlacer"]
