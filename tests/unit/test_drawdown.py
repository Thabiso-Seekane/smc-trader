"""Unit tests for drawdown computation (Week 9).

Drawdown is one of the most important backtest outputs — a strategy that
makes 50% but experiences an 80% drawdown isn't particularly useful. These
tests verify the equity-curve running peak and maximum-drawdown metric.
"""

from datetime import datetime

import pytest

from backtesting.equity_curve import EquityCurve
from backtesting.metrics import PerformanceMetrics


def make_curve(values):
    """Build an EquityCurve from a list of equity values."""
    curve = EquityCurve()
    curve.reset(values[0])
    for i, eq in enumerate(values):
        curve.record(datetime(2024, 1, i + 1), eq, eq)
    return curve


def test_flat_equity_has_zero_drawdown():
    curve = make_curve([10000.0, 10000.0, 10000.0])
    assert curve.max_drawdown == pytest.approx(0.0)


def test_steady_growth_has_zero_drawdown():
    curve = make_curve([10000.0, 10100.0, 10200.0, 10300.0])
    assert curve.max_drawdown == pytest.approx(0.0)


def test_single_decline_drawdown():
    # Peak 10000 -> 9000 = 10% drawdown.
    curve = make_curve([10000.0, 9000.0])
    assert curve.max_drawdown == pytest.approx(0.10)


def test_drawdown_recovers_from_peak():
    # After a drop to 9000, a bounce to 9200 still leaves a drawdown from
    # the 10000 peak, but less than the worst 10%.
    curve = make_curve([10000.0, 9000.0, 9200.0])
    assert curve.max_drawdown == pytest.approx(0.10)
    last = curve.points[-1]
    assert last.drawdown == pytest.approx(1.0 - 9200.0 / 10000.0)


def test_max_drawdown_picks_worst_case():
    # Peak 12000, worst trough 10000 = 16.67%.
    curve = make_curve([12000.0, 11000.0, 10000.0, 13000.0])
    assert curve.max_drawdown == pytest.approx(1.0 - 10000.0 / 12000.0)


def test_metrics_max_drawdown_matches_curve():
    curve = make_curve([10000.0, 8000.0, 12000.0])
    assert PerformanceMetrics.max_drawdown(curve) == pytest.approx(0.20)


def test_drawdown_tracks_peak_not_initial():
    # Initial 10000 then rises to 11000; a drop back to 10050 is only from
    # the 11000 peak, so ~8.6%, not 0%.
    curve = make_curve([10000.0, 11000.0, 10050.0])
    assert curve.max_drawdown == pytest.approx(1.0 - 10050.0 / 11000.0)


def test_drawdown_never_negative():
    curve = make_curve([10000.0, 10500.0])
    for point in curve.points:
        assert point.drawdown >= 0.0


def test_empty_curve_has_zero_drawdown():
    curve = EquityCurve()
    assert curve.max_drawdown == 0.0
