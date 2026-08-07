"""Unit tests for the Week 9 Backtesting enums."""

from backtesting.enums import (
    BacktestStatus,
    Direction,
    ExitReason,
    IntrabarResolution,
    OrderStatus,
    OrderType,
    PositionStatus,
    TradeResultType,
)


def test_order_type_values():
    assert OrderType.MARKET.value == "MARKET"
    assert OrderType.LIMIT.value == "LIMIT"
    assert OrderType.STOP.value == "STOP"


def test_order_status_values():
    assert OrderStatus.PENDING.value == "PENDING"
    assert OrderStatus.FILLED.value == "FILLED"
    assert OrderStatus.CANCELLED.value == "CANCELLED"
    assert OrderStatus.REJECTED.value == "REJECTED"
    assert OrderStatus.EXPIRED.value == "EXPIRED"


def test_position_status_values():
    assert PositionStatus.OPEN.value == "OPEN"
    assert PositionStatus.CLOSED.value == "CLOSED"


def test_direction_values():
    assert Direction.BUY.value == "BUY"
    assert Direction.SELL.value == "SELL"


def test_trade_result_values():
    assert TradeResultType.WIN.value == "WIN"
    assert TradeResultType.LOSS.value == "LOSS"
    assert TradeResultType.BREAKEVEN.value == "BREAKEVEN"
    assert TradeResultType.NO_TRADE.value == "NO_TRADE"


def test_exit_reason_values():
    assert ExitReason.TAKE_PROFIT.value == "TAKE_PROFIT"
    assert ExitReason.STOP_LOSS.value == "STOP_LOSS"
    assert ExitReason.TRAILING_STOP.value == "TRAILING_STOP"
    assert ExitReason.TIME_EXIT.value == "TIME_EXIT"
    assert ExitReason.MANUAL.value == "MANUAL"


def test_intrabar_resolution_values():
    assert IntrabarResolution.CONSERVATIVE.value == "CONSERVATIVE"
    assert IntrabarResolution.OPTIMISTIC.value == "OPTIMISTIC"
    assert IntrabarResolution.BAR_CLOSE.value == "BAR_CLOSE"


def test_backtest_status_values():
    assert BacktestStatus.COMPLETED.value == "COMPLETED"
    assert BacktestStatus.FAILED.value == "FAILED"
