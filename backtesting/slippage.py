"""Slippage model for the Week 9 Backtesting Engine.

Real execution isn't perfect — a market order often fills at a worse price
than expected. This module models fixed slippage as an adverse price
adjustment applied to simulated fills.

For a BUY, slippage raises the effective fill price (worse entry).
For a SELL, slippage lowers the effective fill price (worse entry).
"""

from __future__ import annotations

from dataclasses import dataclass

from backtesting.enums import Direction


@dataclass(slots=True)
class SlippageModel:
    """Apply fixed slippage to a simulated fill price.

    Attributes:
        slippage: Slippage in price units per fill (e.g. 0.20).
        enabled: Whether slippage is applied at all.
    """

    slippage: float = 0.0
    enabled: bool = True

    def apply(self, price: float, direction: Direction) -> float:
        """Return the adverse-adjusted fill price for a given direction.

        Args:
            price: The ideal (quoted) price.
            direction: Buy or sell.

        Returns:
            The fill price including slippage (worse for the trader).
        """
        if not self.enabled or self.slippage <= 0:
            return price
        if direction == Direction.BUY:
            return price + self.slippage
        return price - self.slippage


__all__ = ["SlippageModel"]
