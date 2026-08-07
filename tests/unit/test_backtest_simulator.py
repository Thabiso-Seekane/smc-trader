"""Unit tests for the Week 9 TradeSimulator."""

from datetime import datetime

import pytest

from backtesting.commission import CommissionModel
from backtesting.enums import Direction, ExitReason, IntrabarResolution, OrderType
from backtesting.models import Order
from backtesting.position import PositionManager
from backtesting.simulator import TradeSimulator
from backtesting.slippage import SlippageModel


def make_simulator(resolution="CONSERVATIVE"):
    positions = PositionManager(
        commission=CommissionModel(per_lot=0.0),
        slippage=SlippageModel(slippage=0.0),
    )
    return TradeSimulator(
        intrabar_resolution=resolution,
        positions=positions,
    )


def open_buy(sim, entry=100.0, sl=90.0, tp=120.0, volume=1.0):
    order = Order(
        symbol="XAUUSD",
        direction=Direction.BUY,
        order_type=OrderType.MARKET,
        volume=volume,
    )
    pos = sim.positions.open_position(
        order,
        price=entry,
        stop_loss=sl,
        take_profit=tp,
        risk_amount=10.0,
        timestamp=datetime(2024, 1, 1),
    )
    sim.portfolio.open_position(pos)
    return pos


def test_process_candle_hits_take_profit_buy():
    sim = make_simulator()
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(125.0, 99.0, 124.0, datetime(2024, 1, 2))
    assert len(closed) == 1
    assert closed[0].exit_reason == ExitReason.TAKE_PROFIT
    assert closed[0].profit_loss == pytest.approx(20.0)


def test_process_candle_hits_stop_loss_buy():
    sim = make_simulator()
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(101.0, 89.0, 90.0, datetime(2024, 1, 2))
    assert len(closed) == 1
    assert closed[0].exit_reason == ExitReason.STOP_LOSS
    assert closed[0].profit_loss == pytest.approx(-10.0)


def test_process_candle_no_exit_when_flat():
    sim = make_simulator()
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(110.0, 99.0, 108.0, datetime(2024, 1, 2))
    assert closed == []


def test_conservative_resolves_sl_first():
    sim = make_simulator(IntrabarResolution.CONSERVATIVE.value)
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(125.0, 89.0, 100.0, datetime(2024, 1, 2))
    assert closed[0].exit_reason == ExitReason.STOP_LOSS


def test_optimistic_resolves_tp_first():
    sim = make_simulator(IntrabarResolution.OPTIMISTIC.value)
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(125.0, 89.0, 100.0, datetime(2024, 1, 2))
    assert closed[0].exit_reason == ExitReason.TAKE_PROFIT


def test_bar_close_resolves_at_close():
    sim = make_simulator(IntrabarResolution.BAR_CLOSE.value)
    open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    closed = sim.process_candle(125.0, 89.0, 100.0, datetime(2024, 1, 2))
    assert closed[0].exit_reason == ExitReason.MANUAL
    assert closed[0].exit_price == pytest.approx(100.0)


def test_fill_pending_limit_order():
    sim = make_simulator()
    order = Order(
        symbol="XAUUSD",
        direction=Direction.BUY,
        order_type=OrderType.LIMIT,
        volume=1.0,
        limit_price=100.0,
    )
    sim.orders.submit(order)
    sim.process_candle(110.0, 99.0, 108.0, datetime(2024, 1, 2))
    assert order.is_filled
    assert order.fill_price == pytest.approx(100.0)


def test_sl_tp_helpers():
    sim = make_simulator()
    pos = open_buy(sim, entry=100.0, sl=90.0, tp=120.0)
    assert sim._sl_hit(pos, 89.0, 101.0)
    assert not sim._sl_hit(pos, 95.0, 101.0)
    assert sim._tp_hit(pos, 125.0, 99.0)
    assert not sim._tp_hit(pos, 110.0, 99.0)
