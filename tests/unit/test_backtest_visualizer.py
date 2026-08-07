"""Unit tests for the Week 9 BacktestVisualizer."""

from datetime import datetime

from backtesting.enums import Direction, ExitReason, TradeResultType
from backtesting.models import (
    BacktestConfig,
    BacktestResult,
    EquityPoint,
    Trade,
)
from backtesting.visualizer import BacktestVisualizer


def make_result(with_trades=True):
    trades = []
    if with_trades:
        trades = [
            Trade(
                symbol="XAUUSD",
                direction=Direction.BUY,
                entry_price=100.0,
                exit_price=120.0,
                volume=1.0,
                profit_loss=20.0,
                result=TradeResultType.WIN,
                r_multiple=2.0,
                exit_time=datetime(2024, 1, 15),
                confluence_score=85.0,
                exit_reason=ExitReason.TAKE_PROFIT,
            )
        ]
    return BacktestResult(
        config=BacktestConfig(),
        initial_balance=10000.0,
        final_balance=10020.0,
        equity_curve=[
            EquityPoint(datetime(2024, 1, 1), 10000.0, 10000.0, 0.0),
            EquityPoint(datetime(2024, 1, 2), 10000.0, 10020.0, 0.0),
        ],
        trades=trades,
    )


def test_equity_curve_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.equity_curve(make_result())
    assert fig is not None
    assert fig.to_json()  # serializable


def test_drawdown_curve_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.drawdown_curve(make_result())
    assert fig is not None


def test_r_distribution_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.r_distribution(make_result())
    assert fig is not None


def test_monthly_returns_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.monthly_returns(make_result())
    assert fig is not None


def test_win_loss_distribution_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.win_loss_distribution(make_result())
    assert fig is not None


def test_confluence_vs_performance_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.confluence_vs_performance(make_result())
    assert fig is not None


def test_report_figure_returns_figure():
    viz = BacktestVisualizer()
    fig = viz.report_figure(make_result())
    assert fig is not None


def test_figures_handle_empty_results():
    viz = BacktestVisualizer()
    empty = make_result(with_trades=False)
    assert viz.equity_curve(empty) is not None
    assert viz.drawdown_curve(empty) is not None
    assert viz.r_distribution(empty) is not None
    assert viz.report_figure(empty) is not None
