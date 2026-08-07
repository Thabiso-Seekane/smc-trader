"""Unit tests for the Week 9 Portfolio."""

import pytest

from backtesting.enums import Direction, PositionStatus
from backtesting.models import Position
from backtesting.portfolio import Portfolio


def make_position(entry=100.0, volume=1.0, direction=Direction.BUY, pnl=0.0):
    return Position(
        symbol="XAUUSD",
        direction=direction,
        entry_price=entry,
        volume=volume,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
        profit_loss=pnl,
        status=PositionStatus.OPEN,
    )


def test_reset():
    pf = Portfolio(initial_balance=5000.0)
    pf.reset()
    assert pf.balance == pytest.approx(5000.0)
    assert pf.open_count == 0
    assert pf.closed_count == 0


def test_reset_with_new_balance():
    pf = Portfolio(initial_balance=5000.0)
    pf.reset(10000.0)
    assert pf.initial_balance == pytest.approx(10000.0)
    assert pf.balance == pytest.approx(10000.0)


def test_open_close_position_balance():
    pf = Portfolio(initial_balance=10000.0)
    pos = make_position(pnl=20.0)
    pf.open_position(pos)
    assert pf.open_count == 1
    pf.close_position(pos)
    assert pf.closed_count == 1
    assert pf.balance == pytest.approx(10020.0)


def test_unrealized_pnl():
    pf = Portfolio(initial_balance=10000.0)
    pos = make_position(entry=100.0, volume=2.0)
    pf.open_position(pos)
    assert pf.unrealized_pnl(110.0) == pytest.approx(20.0)


def test_equity():
    pf = Portfolio(initial_balance=10000.0)
    pos = make_position(entry=100.0, volume=2.0)
    pf.open_position(pos)
    assert pf.equity(110.0) == pytest.approx(10020.0)


def test_exposure():
    pf = Portfolio(initial_balance=10000.0)
    pos = make_position(entry=100.0, volume=2.0)
    pf.open_position(pos)
    assert pf.exposure == pytest.approx(200.0)


def test_counts():
    pf = Portfolio(initial_balance=10000.0)
    pos = make_position()
    pf.open_position(pos)
    pf.close_position(pos)
    assert pf.open_count == 0
    assert pf.closed_count == 1
    assert pf.total_positions == 1
