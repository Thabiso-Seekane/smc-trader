"""Unit tests for the Week 9 Backtesting data models."""

from datetime import datetime

import pytest

from backtesting.enums import (
    Direction,
    ExitReason,
    OrderStatus,
    OrderType,
    PositionStatus,
    TradeResultType,
)
from backtesting.models import (
    BacktestConfig,
    BacktestResult,
    EquityPoint,
    Order,
    Position,
    Trade,
)


# --- BacktestConfig -----------------------------------------
def test_config_defaults():
    cfg = BacktestConfig()
    assert cfg.initial_balance == pytest.approx(10_000.0)
    assert cfg.commission == pytest.approx(7.0)
    assert cfg.slippage == pytest.approx(0.0)
    assert cfg.risk_per_trade == pytest.approx(0.01)


# --- Order --------------------------------------------------
def test_order_defaults():
    order = Order()
    assert order.direction == Direction.BUY
    assert order.order_type == OrderType.MARKET
    assert order.status == OrderStatus.PENDING
    assert order.is_buy
    assert not order.is_sell
    assert order.is_pending
    assert not order.is_filled


def test_order_helpers():
    buy = Order(direction=Direction.BUY)
    sell = Order(direction=Direction.SELL)
    assert buy.is_buy
    assert sell.is_sell
    assert not buy.is_sell


# --- Position -----------------------------------------------
def make_position(**kwargs) -> Position:
    defaults = dict(
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_price=100.0,
        volume=1.0,
        stop_loss=90.0,
        take_profit=120.0,
        risk_amount=10.0,
    )
    defaults.update(kwargs)
    return Position(**defaults)


def test_position_helpers():
    long = make_position()
    short = make_position(direction=Direction.SELL)
    assert long.is_buy
    assert long.is_open
    assert not long.is_closed
    assert short.is_sell


def test_position_distances():
    pos = make_position(entry_price=100.0, stop_loss=90.0, take_profit=120.0)
    assert pos.risk_distance == pytest.approx(10.0)
    assert pos.reward_distance == pytest.approx(20.0)
    assert pos.risk_reward == pytest.approx(2.0)


def test_position_risk_reward_zero_when_flat():
    pos = make_position(entry_price=100.0, stop_loss=100.0, take_profit=120.0)
    assert pos.risk_reward == 0.0


def test_position_r_multiple():
    pos = make_position(risk_amount=10.0, profit_loss=20.0)
    assert pos.r_multiple == pytest.approx(2.0)


def test_position_r_multiple_zero_risk():
    pos = make_position(risk_amount=0.0, profit_loss=5.0)
    assert pos.r_multiple == 0.0


def test_position_unrealized_pnl_buy():
    pos = make_position(entry_price=100.0, volume=2.0)
    assert pos.unrealized_pnl(110.0) == pytest.approx(20.0)


def test_position_unrealized_pnl_sell():
    pos = make_position(entry_price=100.0, volume=2.0, direction=Direction.SELL)
    assert pos.unrealized_pnl(90.0) == pytest.approx(20.0)


def test_position_hash_stable():
    pos = make_position()
    assert hash(pos) == hash(pos.id)


# --- Trade --------------------------------------------------
def make_trade(**kwargs) -> Trade:
    defaults = dict(
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_price=100.0,
        exit_price=120.0,
        volume=1.0,
        profit_loss=20.0,
        result=TradeResultType.WIN,
        r_multiple=2.0,
    )
    defaults.update(kwargs)
    return Trade(**defaults)


def test_trade_helpers():
    win = make_trade(result=TradeResultType.WIN, profit_loss=20.0)
    loss = make_trade(result=TradeResultType.LOSS, profit_loss=-10.0)
    assert win.is_win
    assert win.is_profitable
    assert loss.is_loss
    assert not loss.is_profitable


def test_equity_point():
    ts = datetime(2024, 1, 1)
    pt = EquityPoint(timestamp=ts, balance=1000.0, equity=1100.0, drawdown=0.05)
    assert pt.timestamp == ts
    assert pt.balance == pytest.approx(1000.0)
    assert pt.equity == pytest.approx(1100.0)
    assert pt.drawdown == pytest.approx(0.05)


def test_backtest_result_summary():
    cfg = BacktestConfig(initial_balance=1000.0)
    result = BacktestResult(
        config=cfg,
        initial_balance=1000.0,
        final_balance=1100.0,
        total_return=0.1,
        total_trades=5,
        winning_trades=3,
        losing_trades=2,
        win_rate=0.6,
        profit_factor=2.0,
        max_drawdown=0.1,
        sharpe_ratio=1.5,
        average_rr=0.8,
        average_trade=20.0,
        largest_win=50.0,
        largest_loss=-10.0,
        expectancy=20.0,
    )
    s = result.summary
    assert s.initial_balance == pytest.approx(1000.0)
    assert s.final_balance == pytest.approx(1100.0)
    assert s.total_return == pytest.approx(0.1)
    assert s.total_trades == 5
    assert s.winning_trades == 3
    assert s.losing_trades == 2
    assert s.win_rate == pytest.approx(0.6)
    assert s.profit_factor == pytest.approx(2.0)
    assert s.max_drawdown == pytest.approx(0.1)
    assert s.sharpe_ratio == pytest.approx(1.5)
    assert s.average_rr == pytest.approx(0.8)
    assert s.average_trade == pytest.approx(20.0)
    assert s.largest_win == pytest.approx(50.0)
    assert s.largest_loss == pytest.approx(-10.0)
    assert s.expectancy == pytest.approx(20.0)
