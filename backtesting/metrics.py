"""Performance analytics for the Week 9 Backtesting Engine.

The ``PerformanceMetrics`` converts a list of closed :class:`Trade` records
and an equity curve into the headline statistics:

    * Total return
    * Win rate
    * Profit factor
    * Expectancy (currency and R)
    * Average R / median R / best R / worst R
    * Maximum drawdown
    * Sharpe ratio
    * Largest win / loss
    * Average win / average loss
"""

from __future__ import annotations

from dataclasses import dataclass

from backtesting.equity_curve import EquityCurve
from backtesting.models import BacktestResult, PerformanceSummary, Trade


@dataclass(slots=True)
class PerformanceMetrics:
    """Computes performance statistics from trades and an equity curve."""

    def summarize(self, result: BacktestResult) -> PerformanceSummary:
        """Aggregate headline metrics into a :class:`PerformanceSummary`.

        Args:
            result: The backtest result accumulating trades / equity.

        Returns:
            A :class:`PerformanceSummary` with all headline statistics.
        """
        trades = result.trades
        gross_profit = sum(t.profit_loss for t in trades if t.is_profitable)
        gross_loss = abs(
            sum(t.profit_loss for t in trades if not t.is_profitable)
        )
        total_pnl = sum(t.profit_loss for t in trades)

        wins = [t for t in trades if t.is_win]
        losses = [t for t in trades if t.is_loss]
        n = len(trades)

        win_rate = (len(wins) / n) if n else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss else 0.0

        avg_win = (sum(t.profit_loss for t in wins) / len(wins)) if wins else 0.0
        avg_loss = (
            abs(sum(t.profit_loss for t in losses) / len(losses))
            if losses
            else 0.0
        )
        loss_rate = (len(losses) / n) if n else 0.0
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        r_values = [t.r_multiple for t in trades]
        average_rr = (sum(r_values) / len(r_values)) if r_values else 0.0
        expectancy_r = average_rr

        largest_win = max((t.profit_loss for t in trades), default=0.0)
        largest_loss = min((t.profit_loss for t in trades), default=0.0)

        return PerformanceSummary(
            initial_balance=result.initial_balance,
            final_balance=result.final_balance,
            total_return=(result.final_balance - result.initial_balance)
            / result.initial_balance
            if result.initial_balance
            else 0.0,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=result.max_drawdown,
            sharpe_ratio=self.sharpe_ratio(trades),
            average_rr=average_rr,
            average_trade=(total_pnl / n) if n else 0.0,
            largest_win=max(largest_win, 0.0),
            largest_loss=min(largest_loss, 0.0),
            expectancy=expectancy if n else 0.0,
            expectancy_r=expectancy_r,
        )

    @staticmethod
    def total_return(initial: float, final: float) -> float:
        """Return the fractional total return."""
        if initial <= 0:
            return 0.0
        return (final - initial) / initial

    @staticmethod
    def win_rate(trades: list[Trade]) -> float:
        """Return the fraction of trades that won."""
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t.is_win)
        return wins / len(trades)

    @staticmethod
    def profit_factor(trades: list[Trade]) -> float:
        """Return gross profit / gross loss."""
        gross_profit = sum(t.profit_loss for t in trades if t.is_profitable)
        gross_loss = abs(
            sum(t.profit_loss for t in trades if not t.is_profitable)
        )
        if gross_profit == 0 and gross_loss == 0:
            return 0.0
        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @staticmethod
    def expectancy_r(trades: list[Trade]) -> float:
        """Return the average R-multiple per trade."""
        if not trades:
            return 0.0
        return sum(t.r_multiple for t in trades) / len(trades)

    @staticmethod
    def average_r(trades: list[Trade]) -> float:
        """Alias for :meth:`expectancy_r` (average R per trade)."""
        return PerformanceMetrics.expectancy_r(trades)

    @staticmethod
    def best_r(trades: list[Trade]) -> float:
        """Return the best (largest) R-multiple."""
        if not trades:
            return 0.0
        return max(t.r_multiple for t in trades)

    @staticmethod
    def worst_r(trades: list[Trade]) -> float:
        """Return the worst (smallest) R-multiple."""
        if not trades:
            return 0.0
        return min(t.r_multiple for t in trades)

    @staticmethod
    def sharpe_ratio(trades: list[Trade], risk_free: float = 0.0) -> float:
        """Return the Sharpe ratio from per-trade returns.

        Uses the R-multiple series as the return series. With fewer than 2
        trades or zero variance the ratio is 0.

        Args:
            trades: The closed trades.
            risk_free: The risk-free rate (applied to the mean only).

        Returns:
            The Sharpe ratio.
        """
        if len(trades) < 2:
            return 0.0
        returns = [t.r_multiple for t in trades]
        mean = sum(returns) / len(returns)
        var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        if var <= 0:
            return 0.0
        std = var ** 0.5
        return (mean - risk_free) / std

    @staticmethod
    def max_drawdown(curve: EquityCurve) -> float:
        """Return the maximum drawdown (fraction) from an equity curve."""
        return curve.max_drawdown

    @staticmethod
    def monthly_returns(trades: list[Trade]) -> dict[str, float]:
        """Return a mapping of ``YYYY-MM`` -> total P&L for that month.

        Args:
            trades: The closed trades.

        Returns:
            A dict keyed by month label with the summed P&L.
        """
        out: dict[str, float] = {}
        for trade in trades:
            key = trade.exit_time.strftime("%Y-%m")
            out[key] = out.get(key, 0.0) + trade.profit_loss
        return dict(sorted(out.items()))


__all__ = ["PerformanceMetrics"]
