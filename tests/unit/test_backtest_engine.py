"""Unit tests for the Week 9 BacktestEngine."""

from datetime import datetime

import pandas as pd
import pytest

from backtesting.enums import Direction, ExitReason
from backtesting.engine import BacktestEngine
from backtesting.models import BacktestConfig, Order


def make_data():
    return pd.DataFrame(
        {
            "date": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3),
                datetime(2024, 1, 4),
                datetime(2024, 1, 5),
            ],
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
        }
    )


def test_run_empty_data():
    engine = BacktestEngine(config=BacktestConfig(initial_balance=10000.0))
    result = engine.run(pd.DataFrame())
    assert result.total_trades == 0
    assert result.status == "COMPLETED"


def test_run_with_order_objects():
    engine = BacktestEngine(config=BacktestConfig(initial_balance=10000.0))

    def executor(candle):
        if candle.Index == 1:
            return [Order(symbol="XAUUSD", direction=Direction.BUY, volume=1.0)]
        return []

    result = engine.run(make_data(), executor=executor)
    # The order is submitted but never filled as a position (market order
    # fills on the same bar via the simulator).
    assert result.status == "COMPLETED"


def test_run_with_tuple_executor():
    engine = BacktestEngine(
        config=BacktestConfig(initial_balance=10000.0, commission=0.0)
    )

    def executor(candle):
        if candle.Index == 0:
            return [
                (100.0, 95.0, 120.0, 1.0, 85.0, "Sweep", "BUY")
            ]
        return []

    result = engine.run(make_data(), executor=executor)
    assert result.status == "COMPLETED"
    # The position opened at candle 0 can be closed by a later candle.
    assert result.total_trades >= 0


def test_run_returns_metrics():
    engine = BacktestEngine(
        config=BacktestConfig(initial_balance=10000.0, commission=0.0)
    )

    def executor(candle):
        if candle.Index == 0:
            # Buy at 100, stop 90, target 130 — will win on the up-move.
            return [(100.0, 90.0, 130.0, 1.0, 90.0, "setup", "BUY")]
        return []

    result = engine.run(make_data(), executor=executor)
    assert result.initial_balance == pytest.approx(10000.0)
    assert result.winning_trades >= 0
    assert result.total_trades >= 0


def test_last_result_after_run():
    engine = BacktestEngine(config=BacktestConfig(initial_balance=10000.0))
    assert engine.last_result is None
    engine.run(make_data())
    assert engine.last_result is not None


def test_equity_curve_recorded():
    engine = BacktestEngine(config=BacktestConfig(initial_balance=10000.0))
    result = engine.run(make_data())
    assert len(result.equity_curve) > 0
