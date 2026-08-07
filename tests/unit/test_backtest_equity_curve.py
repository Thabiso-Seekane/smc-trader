"""Unit tests for the Week 9 EquityCurve."""

from datetime import datetime

import pytest

from backtesting.equity_curve import EquityCurve


def test_reset():
    curve = EquityCurve()
    curve.reset(1000.0)
    assert curve.count == 0
    assert curve.peak == pytest.approx(1000.0)


def test_record_appends():
    curve = EquityCurve()
    curve.reset(1000.0)
    curve.record(datetime(2024, 1, 1), 1000.0, 1000.0)
    curve.record(datetime(2024, 1, 2), 1000.0, 1100.0)
    assert curve.count == 2
    assert curve.final_equity == pytest.approx(1100.0)


def test_drawdown_computed():
    curve = EquityCurve()
    curve.reset(1000.0)
    curve.record(datetime(2024, 1, 1), 1000.0, 1000.0)
    curve.record(datetime(2024, 1, 2), 1000.0, 1200.0)  # new peak
    curve.record(datetime(2024, 1, 3), 1000.0, 900.0)  # drawdown
    assert curve.max_drawdown == pytest.approx(0.25)


def test_max_drawdown_empty():
    curve = EquityCurve()
    assert curve.max_drawdown == 0.0
    assert curve.final_equity == 0.0


def test_len():
    curve = EquityCurve()
    curve.reset(1000.0)
    curve.record(datetime(2024, 1, 1), 1000.0, 1000.0)
    assert len(curve) == 1
