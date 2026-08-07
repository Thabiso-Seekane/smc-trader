"""Strategy attribution for the Week 9 Backtesting Engine.

The ``BacktestAnalyzer`` breaks down backtest performance by confluence
score band. Since Week 7 produces a 0-100 confluence score per setup, we can
empirically test whether "higher confluence = better trades".

This avoids blindly trusting the scoring system — it measures it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtesting.models import Trade


@dataclass(slots=True)
class ConfluenceBand:
    """Aggregated performance for a confluence-score band.

    Attributes:
        label: Human-readable band label (e.g. "70-79").
        trades: Number of trades in this band.
        win_rate: Fraction of trades in the band that won.
        average_r: Average R-multiple in the band.
        total_pnl: Total realized P&L in the band.
    """

    label: str = ""
    trades: int = 0
    win_rate: float = 0.0
    average_r: float = 0.0
    total_pnl: float = 0.0


@dataclass(slots=True)
class BacktestAnalyzer:
    """Groups trades by confluence score and computes per-band metrics.

    Attributes:
        bands: The confluence score bands used for attribution.
    """

    bands: list[tuple[float, float, str]] = field(
        default_factory=lambda: [
            (70.0, 79.0, "70-79"),
            (80.0, 89.0, "80-89"),
            (90.0, 100.0, "90-100"),
        ]
    )

    def confluence_attribution(self, trades: list[Trade]) -> list[ConfluenceBand]:
        """Compute per-band performance across the given trades.

        Args:
            trades: The closed trades.

        Returns:
            A list of :class:`ConfluenceBand` (one per configured band).
        """
        result: list[ConfluenceBand] = []
        for lo, hi, label in self.bands:
            band_trades = [
                t for t in trades if lo <= t.confluence_score <= hi
            ]
            result.append(self._summarize_band(label, band_trades))
        return result

    @staticmethod
    def _summarize_band(
        label: str,
        trades: list[Trade],
    ) -> ConfluenceBand:
        """Summarize a list of trades into a single band metric."""
        n = len(trades)
        if n == 0:
            return ConfluenceBand(label=label)
        wins = sum(1 for t in trades if t.is_win)
        avg_r = sum(t.r_multiple for t in trades) / n
        total_pnl = sum(t.profit_loss for t in trades)
        return ConfluenceBand(
            label=label,
            trades=n,
            win_rate=wins / n,
            average_r=avg_r,
            total_pnl=total_pnl,
        )


__all__ = ["ConfluenceBand", "BacktestAnalyzer"]
