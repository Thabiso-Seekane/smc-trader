"""Commission model for the Week 9 Backtesting Engine.

A commission is charged per lot (or unit) on both open and close. The exact
value depends on the broker / instrument. This module keeps the simulation
realistic by subtracting commission from realized P&L.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CommissionModel:
    """Compute commission charges for a trade.

    Attributes:
        per_lot: Commission in currency units per lot (e.g. 7.0).
        enabled: Whether commission is applied at all.
    """

    per_lot: float = 7.0
    enabled: bool = True

    def charge(self, volume: float) -> float:
        """Return the total commission (open + close) for a given volume.

        Args:
            volume: The traded lot / unit size.

        Returns:
            The commission in currency units (already doubled for open+close).
        """
        if not self.enabled:
            return 0.0
        return 2.0 * self.per_lot * volume

    def open_cost(self, volume: float) -> float:
        """Return the commission charged on the open leg."""
        if not self.enabled:
            return 0.0
        return self.per_lot * volume

    def close_cost(self, volume: float) -> float:
        """Return the commission charged on the close leg."""
        return self.open_cost(volume)


__all__ = ["CommissionModel"]
