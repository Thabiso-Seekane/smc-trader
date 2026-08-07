"""Unit tests for the Week 9 PerformanceMetrics."""

from datetime import datetime

import pytest

from backtesting.enums import Direction, TradeResultType
from backtesting.equity_curve import EquityCurve
from backtesting.models import BacktestResult, Trade
from backtesting.metrics import PerformanceMetrics


def make_trade(pnl, r=1.0, result=None, exit_time=None):
    if result is None:
        result = TradeResultType.WIN if pnl > 0 else TradeResultType.LOSS
    return Trade(
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_price=100.0,
        exit_price=100.0 + pnl,
        volume=1.0,
        profit_loss=float(pnl),
        result=result,
        r_multiple=float(r),
        exit_time=exit_time or datetime(2024, 1, 15),
    )


def test_win_rate():
    trades = [
        make_trade(10.0, result=TradeResultType.WIN),
        make_trade(-5.0, result=TradeResultType.LOSS),
        make_trade(3.0, result=TradeResultType.WIN),
    ]
    assert PerformanceMetrics.win_rate(trades) == pytest.approx(2 / 3)


def test_win_rate_empty():
    assert PerformanceMetrics.win_rate([]) == 0.0


def test_profit_factor():
    trades = [
        make_trade(100.0, result=TradeResultType.WIN),
        make_trade(-50.0, result=TradeResultType.LOSS),
    ]
    assert PerformanceMetrics.profit_factor(trades) == pytest.approx(2.0)


def test_profit_factor_no_losses():
    trades = [make_trade(10.0, result=TradeResultType.WIN)]
    assert PerformanceMetrics.profit_factor(trades) == pytest.approx(10.0)


def test_expectancy_r():
    trades = [
        make_trade(10.0, r=2.0),
        make_trade(-5.0, r=-1.0),
    ]
    assert PerformanceMetrics.expectancy_r(trades) == pytest.approx(0.5)
    assert PerformanceMetrics.average_r(trades) == pytest.approx(0.5)


def test_best_worst_r():
    trades = [
        make_trade(10.0, r=2.0),
        make_trade(-5.0, r=-1.0),
        make_trade(7.0, r=1.5),
    ]
    assert PerformanceMetrics.best_r(trades) == pytest.approx(2.0)
    assert PerformanceMetrics.worst_r(trades) == pytest.approx(-1.0)


def test_sharpe_ratio():
    trades = [
        make_trade(10.0, r=1.0),
        make_trade(20.0, r=2.0),
        make_trade(30.0, r=3.0),
    ]
    assert PerformanceMetrics.sharpe_ratio(trades) == pytest.approx(2.0)


def test_sharpe_ratio_fewer_than_2():
    trades = [make_trade(10.0, r=1.0)]
    assert PerformanceMetrics.sharpe_ratio(trades) == 0.0


def test_max_drawdown():
    curve = EquityCurve()
    curve.reset(1000.0)
    curve.record(datetime(2024, 1, 1), 1000.0, 1000.0)
    curve.record(datetime(2024, 1, 2), 1000.0, 1200.0)
    curve.record(datetime(2024, 1, 3), 1000.0, 900.0)
    assert PerformanceMetrics.max_drawdown(curve) == pytest.approx(0.25)


def test_monthly_returns():
    trades = [
        make_trade(10.0, exit_time=datetime(2024, 1, 15)),
        make_trade(-5.0, exit_time=datetime(2024, 1, 20)),
        make_trade(7.0, exit_time=datetime(2024, 2, 2)),
    ]
    monthly = PerformanceMetrics.monthly_returns(trades)
    assert monthly["2024-01"] == pytest.approx(5.0)
    assert monthly["2024-02"] == pytest.approx(7.0)


def test_summarize():
    trades = [
        make_trade(100.0, r=2.0, result=TradeResultType.WIN),
        make_trade(-50.0, r=-1.0, result=TradeResultType.LOSS),
    ]
    result = BacktestResult(
        initial_balance=1000.0,
        final_balance=1050.0,
        trades=trades,
    )
    summary = PerformanceMetrics().summarize(result)
    assert summary.total_trades == 2
    assert summary.total_return == pytest.approx(0.05)
    assert summary.winning_trades == 1
    assert summary.losing_trades == 1
    assert summary.average_rr == pytest.approx(0.5)

