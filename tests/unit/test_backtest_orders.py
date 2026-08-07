"""Unit tests for the Week 9 OrderManager."""

import pytest

from backtesting.enums import Direction, OrderStatus, OrderType
from backtesting.models import Order
from backtesting.orders import OrderManager


def make_order(order_type=OrderType.MARKET, direction=Direction.BUY, **kw) -> Order:
    return Order(
        symbol="XAUUSD",
        direction=direction,
        order_type=order_type,
        volume=1.0,
        limit_price=kw.get("limit_price"),
        stop_price=kw.get("stop_price"),
    )


def test_submit_sets_pending():
    mgr = OrderManager()
    order = make_order()
    mgr.submit(order)
    assert order.status == OrderStatus.PENDING
    assert mgr.pending_count() == 1


def test_fill_market():
    mgr = OrderManager()
    order = make_order()
    mgr.submit(order)
    mgr.fill_market(order, 100.0)
    assert order.is_filled
    assert order.fill_price == pytest.approx(100.0)
    assert mgr.pending_count() == 0
    assert len(mgr.filled) == 1


def test_cancel():
    mgr = OrderManager()
    order = make_order()
    mgr.submit(order)
    mgr.cancel(order)
    assert order.status == OrderStatus.CANCELLED
    assert mgr.pending_count() == 0
    assert len(mgr.cancelled) == 1


def test_reject():
    mgr = OrderManager()
    order = make_order()
    mgr.submit(order)
    mgr.reject(order, reason="margin")
    assert order.status == OrderStatus.REJECTED
    assert order.reason == "margin"
    assert mgr.pending_count() == 0


def test_should_fill_market_always():
    mgr = OrderManager()
    order = make_order()
    assert mgr.should_fill(order, 100.0, 90.0)


def test_should_fill_limit_buy():
    mgr = OrderManager()
    order = make_order(OrderType.LIMIT, Direction.BUY, limit_price=100.0)
    assert mgr.should_fill(order, 110.0, 99.0)
    assert not mgr.should_fill(order, 110.0, 101.0)


def test_should_fill_limit_sell():
    mgr = OrderManager()
    order = make_order(OrderType.LIMIT, Direction.SELL, limit_price=100.0)
    assert mgr.should_fill(order, 101.0, 90.0)
    assert not mgr.should_fill(order, 99.0, 90.0)


def test_should_fill_stop_buy():
    mgr = OrderManager()
    order = make_order(OrderType.STOP, Direction.BUY, stop_price=100.0)
    assert mgr.should_fill(order, 101.0, 95.0)
    assert not mgr.should_fill(order, 99.0, 95.0)


def test_should_fill_stop_sell():
    mgr = OrderManager()
    order = make_order(OrderType.STOP, Direction.SELL, stop_price=100.0)
    assert mgr.should_fill(order, 105.0, 99.0)
    assert not mgr.should_fill(order, 105.0, 101.0)
