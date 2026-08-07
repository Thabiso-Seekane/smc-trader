"""Equity-curve tracking for the Week 9 Backtesting Engine.

The ``EquityCurve`` records :class:`EquityPoint` snapshots as the backtest
advances. It also computes the running drawdown from the equity peak, which
feeds the maximum-drawdown metric.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtesting.models import EquityPoint


@dataclass(slots=True)
class EquityCurve:
    """Append-only collection of equity snapshots.

    Attributes:
        points: The recorded :class:`EquityPoint` snapshots.
        peak: The running equity peak seen so far.
    """

    points: list[EquityPoint] = field(default_factory=list)
    peak: float = 0.0

    def reset(self, initial_balance: float) -> None:
        """Clear the curve and seed the peak from a starting balance.

        Args:
            initial_balance: The starting balance used as the initial peak.
        """
        self.points = []
        self.peak = initial_balance

    def record(
        self,
        timestamp: datetime,
        balance: float,
        equity: float,
    ) -> EquityPoint:
        """Record a new equity snapshot.

        Args:
            timestamp: When the snapshot is taken.
            balance: Realized cash balance.
            equity: Balance + unrealized P&L.

        Returns:
            The created :class:`EquityPoint`.
        """
        self.peak = max(self.peak, equity)
        drawdown = (self.peak - equity) / self.peak if self.peak > 0 else 0.0
        point = EquityPoint(
            timestamp=timestamp,
            balance=balance,
            equity=equity,
            drawdown=drawdown,
        )
        self.points.append(point)
        return point

    @property
    def count(self) -> int:
        """Return the number of recorded points."""
        return len(self.points)

    @property
    def max_drawdown(self) -> float:
        """Return the worst drawdown (fraction) across all points."""
        if not self.points:
            return 0.0
        return max(p.drawdown for p in self.points)

    @property
    def final_equity(self) -> float:
        """Return the equity of the last recorded point (0 if none)."""
        if not self.points:
            return 0.0
        return self.points[-1].equity

    def __len__(self) -> int:
        return self.count


__all__ = ["EquityCurve"]
