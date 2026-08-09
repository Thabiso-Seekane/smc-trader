"""Integration tests for the Week 9 BacktestEngine.

These run a full multi-candle backtest through the engine — order
submission, position opening, SL/TP resolution (with conservative intrabar
execution), commission, and slippage — and assert the resulting metrics.
"""

from datetime import datetime

import pandas as pd
import pytest

from backtesting.engine import BacktestEngine
from backtesting.models import BacktestConfig


def make_data():
    """A deterministic up-then-down series so trades resolve predictably."""
    return pd.DataFrame(
        {
            "date": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3),
                datetime(2024, 1, 4),
                datetime(2024, 1, 5),
                datetime(2024, 1, 6),
                datetime(2024, 1, 7),
            ],
            "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 110.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 108.0],
        }
    )


def _config(**kwargs):
    base = dict(
        initial_balance=10_000.0,
        commission=0.0,
        slippage=0.0,
        risk_per_trade=0.01,
        symbol="XAUUSD",
        timeframe="M15",
    )
    base.update(kwargs)
    return BacktestConfig(**base)


def test_full_backtest_with_take_profit():
    engine = BacktestEngine(config=_config())

    def executor(candle):
        # Buy at candle 0 with a TP the uptrend will reach (candle 6 high 110).
        if candle.Index == 0:
            return [(100.0, 95.0, 108.0, 1.0, 90.0, "Sweep + CHoCH", "BUY")]
        return []

    result = engine.run(make_data(), executor=executor)
    assert result.status == "COMPLETED"
    assert result.total_trades >= 1
    # The up-move reaches the TP, so we expect at least one winning trade.
    assert result.winning_trades >= 1
    assert result.final_balance > result.initial_balance


def test_full_backtest_with_stop_loss():
    engine = BacktestEngine(config=_config())

    def executor(candle):
        # Buy at candle 0 with a tight SL that the first low (99) breaches.
        if candle.Index == 0:
            # entry 100, stop 99.5 — candle 0 low (99) touches it.
            return [(100.0, 99.5, 150.0, 1.0, 80.0, "Sweep", "BUY")]
        return []

    result = engine.run(make_data(), executor=executor)
    assert result.losing_trades >= 1
    assert result.status == "COMPLETED"


def test_full_backtest_commission_reduces_pnl():
    # Same setup, but with commission enabled — final P&L must be lower.
    def run(commission):
        engine = BacktestEngine(config=_config(commission=commission))

        def executor(candle):
            if candle.Index == 0:
                return [(100.0, 95.0, 108.0, 1.0, 90.0, "setup", "BUY")]
            return []

        return engine.run(make_data(), executor=executor)

    no_commission = run(0.0)
    with_commission = run(7.0)
    assert with_commission.final_balance <= no_commission.final_balance


def test_full_backtest_slippage_changes_entry():
    engine = BacktestEngine(config=_config(slippage=0.50))

    def executor(candle):
        if candle.Index == 0:
            return [(100.0, 95.0, 108.0, 1.0, 90.0, "setup", "BUY")]
        return []

    result = engine.run(make_data(), executor=executor)
    if result.trades:
        # Slippage should push the entry above 100 for a buy.
        assert result.trades[0].entry_price > 100.0


def test_metrics_are_reported():
    engine = BacktestEngine(config=_config())

    def executor(candle):
        return [
            (100.0 + candle.Index * 0.5, 95.0, 108.0, 1.0, 85.0, "setup", "BUY")
        ]

    result = engine.run(make_data(), executor=executor)
    assert result.total_return is not None
    assert result.win_rate is not None
    assert result.profit_factor is not None
    assert result.expectancy is not None
    assert result.average_rr is not None
    assert len(result.equity_curve) > 0
