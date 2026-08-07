"""Backtest Engine — the public façade for Week 9.

``BacktestEngine`` is the single entry point for running a backtest. It
replays historical OHLC candles **sequentially** (never looking ahead),
filling orders, resolving positions, tracking a portfolio, and computing
performance analytics.

The engine consumes:
    * Historical OHLC ``DataFrame`` (columns: ``date``, ``high``, ``low``,
      ``close``).
    * A callable ``executor`` that, given the current candle, returns a list
      of :class:`Order` objects (or raw tuples) to submit.

The engine is intentionally **independent of MT5**. It simulates execution
itself; MT5 is only for data in Week 9 and live execution in Week 11.

              Strategy
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Backtest Engine   Paper Engine
        │                 │
        ▼                 ▼
   Simulator            MT5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from backtesting.commission import CommissionModel
from backtesting.equity_curve import EquityCurve
from backtesting.metrics import PerformanceMetrics
from backtesting.models import BacktestConfig, BacktestResult, Order
from backtesting.enums import Direction
from backtesting.orders import OrderManager
from backtesting.portfolio import Portfolio
from backtesting.position import PositionManager
from backtesting.slippage import SlippageModel
from backtesting.simulator import TradeSimulator


@dataclass(slots=True)
class BacktestEngine:
    """Runs a deterministic, event-driven backtest.

    Attributes:
        config: The :class:`BacktestConfig` for the run.
        commission: The :class:`CommissionModel`.
        slippage: The :class:`SlippageModel`.
        portfolio: The :class:`Portfolio`.
        orders: The :class:`OrderManager`.
        positions: The :class:`PositionManager`.
        simulator: The :class:`TradeSimulator`.
        equity_curve: The :class:`EquityCurve`.
        metrics: The :class:`PerformanceMetrics`.
        last_result: The most recent :class:`BacktestResult`, if any.
    """

    config: BacktestConfig = field(default_factory=BacktestConfig)
    commission: CommissionModel = field(default=None, init=False, repr=False)
    slippage: SlippageModel = field(default=None, init=False, repr=False)
    portfolio: Portfolio = field(default=None, init=False, repr=False)
    orders: OrderManager = field(default=None, init=False, repr=False)
    positions: PositionManager = field(default=None, init=False, repr=False)
    simulator: TradeSimulator = field(default=None, init=False, repr=False)
    equity_curve: EquityCurve = field(default=None, init=False, repr=False)
    metrics: PerformanceMetrics = field(default=None, init=False, repr=False)
    last_result: BacktestResult | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Reset the run state from the config."""
        self._reset()

    def _reset(self) -> None:
        """Build fresh sub-components for a new run."""
        self.commission = CommissionModel(per_lot=self.config.commission)
        self.slippage = SlippageModel(slippage=self.config.slippage)
        self.portfolio = Portfolio(initial_balance=self.config.initial_balance)
        self.portfolio.reset(self.config.initial_balance)
        self.orders = OrderManager()
        self.positions = PositionManager(
            commission=self.commission, slippage=self.slippage
        )
        self.simulator = TradeSimulator(
            orders=self.orders,
            positions=self.positions,
            portfolio=self.portfolio,
            intrabar_resolution=self.config.intrabar_resolution,
        )
        self.equity_curve = EquityCurve()
        self.equity_curve.reset(self.config.initial_balance)
        self.metrics = PerformanceMetrics()
        self.last_result = None

    def run(
        self,
        data: pd.DataFrame,
        executor=None,
    ) -> BacktestResult:
        """Run the backtest over a historical OHLC DataFrame.

        Candles are processed in order. For each candle the ``executor`` is
        called with the current candle row and may return a list of orders
        (or raw tuples) to submit. The simulator then fills orders and
        resolves positions for that bar. **No future data is accessible.**

        Args:
            data: OHLCV DataFrame with ``date``, ``high``, ``low``, ``close``.
            executor: Optional callable taking the current candle row and
                returning a list of :class:`Order` objects, or a list of
                tuples ``(entry, stop, target, volume[, confluence, reason,
                direction])``.

        Returns:
            A fully populated :class:`BacktestResult`.
        """
        self._reset()
        if data is None or data.empty:
            result = self._build_result()
            self.last_result = result
            return result

        for row in data.itertuples(index=True):
            ts = getattr(row, "date", None)
            high = float(getattr(row, "high", 0.0))
            low = float(getattr(row, "low", 0.0))
            close = float(getattr(row, "close", 0.0))

            if executor is not None:
                orders = executor(row)
                self._submit_orders(orders, ts)

            # Mark-to-market *before* resolving exits this bar.
            self.equity_curve.record(
                ts or datetime.now(),
                self.portfolio.balance,
                self.portfolio.equity(close),
            )

            # Process the bar: fill pending orders and resolve exits.
            self.simulator.process_candle(high, low, close, ts)

        # Final equity snapshot.
        last_close = (
            float(data["close"].iloc[-1]) if "close" in data else 0.0
        )
        self.equity_curve.record(
            datetime.now(),
            self.portfolio.balance,
            self.portfolio.equity(last_close),
        )

        result = self._build_result()
        self.last_result = result
        return result

    def _submit_orders(self, orders, timestamp) -> None:
        """Submit orders produced by the executor.

        Supports:
            * a list of :class:`Order` objects, or
            * a list of tuples ``(entry, stop, target, volume[, confluence,
              reason, direction])``.
        """
        if not orders:
            return
        for item in orders:
            if isinstance(item, Order):
                self.orders.submit(item)
                continue
            entry, stop, target, volume = item[0], item[1], item[2], item[3]
            confluence = float(item[4]) if len(item) > 4 else 0.0
            reason = str(item[5]) if len(item) > 5 else ""
            direction = item[6] if len(item) > 6 else "BUY"
            direction_enum = (
                direction
                if isinstance(direction, Direction)
                else Direction.BUY
                if str(direction).upper() == "BUY"
                else Direction.SELL
            )
            order = Order(
                symbol=self.config.symbol,
                direction=direction_enum,
                volume=float(volume),
                reason=reason,
            )
            self.orders.submit(order)
            pos = self.positions.open_position(
                order,
                price=float(entry),
                stop_loss=float(stop),
                take_profit=float(target),
                risk_amount=self._risk_amount(
                    float(volume), float(stop), float(target)
                ),
                timestamp=timestamp,
                confluence_score=confluence,
                reason=reason,
            )
            self.portfolio.open_position(pos)

    @staticmethod
    def _risk_amount(volume: float, stop: float, target: float) -> float:
        """Estimate the currency risked for a raw order tuple."""
        if stop == target:
            return 0.0
        return abs(target - stop) * volume

    def _build_result(self) -> BacktestResult:
        """Assemble the final :class:`BacktestResult`."""
        trades = self.positions.trades
        final_balance = self.portfolio.balance
        provisional = BacktestResult(
            config=self.config,
            initial_balance=self.config.initial_balance,
            final_balance=final_balance,
            trades=trades,
            equity_curve=self.equity_curve.points,
        )
        summary = self.metrics.summarize(provisional)
        return BacktestResult(
            config=self.config,
            initial_balance=self.config.initial_balance,
            final_balance=final_balance,
            total_return=summary.total_return,
            total_trades=summary.total_trades,
            winning_trades=summary.winning_trades,
            losing_trades=summary.losing_trades,
            win_rate=summary.win_rate,
            profit_factor=summary.profit_factor,
            max_drawdown=summary.max_drawdown,
            sharpe_ratio=summary.sharpe_ratio,
            average_rr=summary.average_rr,
            average_trade=summary.average_trade,
            largest_win=summary.largest_win,
            largest_loss=summary.largest_loss,
            expectancy=summary.expectancy,
            equity_curve=self.equity_curve.points,
            trades=trades,
            positions=self.portfolio.closed_positions,
            status="COMPLETED",
        )


__all__ = ["BacktestEngine"]
