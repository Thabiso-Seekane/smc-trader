"""Unit tests for the Week 9 PositionManager."""

import pytest

from backtesting.commission import CommissionModel
from backtesting.enums import Direction, ExitReason, PositionStatus, TradeResultType
from backtesting.models import Order
from backtesting.position import PositionManager
from backtesting.slippage import SlippageModel


def make_position_manager(slippage=0.0, commission=0.0):
    return PositionManager(
        commission=CommissionModel(per_lot=commission),
        slippage=SlippageModel(slippage=slippage),
    )


def make_buy_order():
    return Order(
        symbol="XAUUSD",
        direction=Direction.BUY,
        volume=1.0,
    )


def test_open_position_applies_slippage():
    mgr = make_position_manager(slippage=0.5)
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    assert pos.entry_price == pytest.approx(100.5)
    assert pos.is_open
    assert len(mgr.open_positions) == 1


def test_open_position_no_slippage():
    mgr = make_position_manager()
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    assert pos.entry_price == pytest.approx(100.0)


def test_update_mfe_mae_buy():
    mgr = make_position_manager()
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    mgr.update(pos, 110.0, 95.0)
    assert pos.mfe == pytest.approx(10.0)
    assert pos.mae == pytest.approx(-5.0)


def test_update_mfe_mae_sell():
    mgr = make_position_manager()
    order = Order(symbol="XAUUSD", direction=Direction.SELL, volume=1.0)
    pos = mgr.open_position(
        order,
        price=100.0,
        stop_loss=110.0,
        take_profit=80.0,
        risk_amount=10.0,
    )
    mgr.update(pos, 105.0, 90.0)
    assert pos.mfe == pytest.approx(10.0)
    assert pos.mae == pytest.approx(-5.0)


def test_close_position_buy_profit():
    mgr = make_position_manager()
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    trade = mgr.close_position(pos, 120.0, ExitReason.TAKE_PROFIT)
    assert pos.is_closed
    assert pos.profit_loss == pytest.approx(20.0)
    assert trade.result == TradeResultType.WIN
    assert trade.r_multiple == pytest.approx(2.0)
    assert len(mgr.closed_positions) == 1
    assert len(mgr.trades) == 1


def test_close_position_buy_loss():
    mgr = make_position_manager()
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    trade = mgr.close_position(pos, 90.0, ExitReason.STOP_LOSS)
    assert trade.result == TradeResultType.LOSS
    assert trade.profit_loss == pytest.approx(-10.0)
    assert trade.r_multiple == pytest.approx(-1.0)


def test_close_position_sell_profit():
    mgr = make_position_manager()
    order = Order(symbol="XAUUSD", direction=Direction.SELL, volume=1.0)
    pos = mgr.open_position(
        order,
        price=100.0,
        stop_loss=110.0,
        take_profit=80.0,
        risk_amount=10.0,
    )
    trade = mgr.close_position(pos, 80.0, ExitReason.TAKE_PROFIT)
    assert trade.result == TradeResultType.WIN
    assert trade.profit_loss == pytest.approx(20.0)


def test_close_position_with_commission():
    mgr = make_position_manager(commission=5.0)
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    trade = mgr.close_position(pos, 120.0, ExitReason.TAKE_PROFIT)
    # raw P&L = 20; commission = 2 * 5 * 1 = 10
    assert trade.profit_loss == pytest.approx(10.0)
    assert trade.commission == pytest.approx(10.0)


def test_classify_breakeven():
    mgr = make_position_manager()
    pos = mgr.open_position(
        make_buy_order(),
        price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    trade = mgr.close_position(pos, 100.0, ExitReason.MANUAL)
    assert trade.result == TradeResultType.BREAKEVEN
