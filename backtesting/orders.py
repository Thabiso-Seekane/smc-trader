"""Order management for the Week 9 Backtesting Engine.

The ``OrderManager`` is responsible for the order lifecycle: creating
orders, tracking pending orders, filling them at a market price, and
cancelling / rejecting them. It keeps the engine's order book.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtesting.enums import OrderStatus, OrderType
from backtesting.models import Order


@dataclass(slots=True)
class OrderManager:
    """Tracks and fills orders.

    Attributes:
        pending: In-flight orders not yet filled.
        filled: Orders that produced a position.
        cancelled: Orders that were cancelled or rejected.
    """

    pending: list[Order] = field(default_factory=list)
    filled: list[Order] = field(default_factory=list)
    cancelled: list[Order] = field(default_factory=list)

    def submit(self, order: Order) -> Order:
        """Register a new pending order.

        Args:
            order: The order to submit.

        Returns:
            The same order (now pending).
        """
        order.status = OrderStatus.PENDING
        self.pending.append(order)
        return order

    def cancel(self, order: Order) -> Order:
        """Cancel a pending order.

        Args:
            order: The order to cancel.

        Returns:
            The order (now cancelled).
        """
        if order in self.pending:
            self.pending.remove(order)
        order.status = OrderStatus.CANCELLED
        if order not in self.cancelled:
            self.cancelled.append(order)
        return order

    def reject(self, order: Order, reason: str = "") -> Order:
        """Reject a pending order (e.g. risk / margin violation).

        Args:
            order: The order to reject.
            reason: Optional rejection reason.

        Returns:
            The order (now rejected).
        """
        if order in self.pending:
            self.pending.remove(order)
        order.status = OrderStatus.REJECTED
        if reason:
            order.reason = reason
        if order not in self.cancelled:
            self.cancelled.append(order)
        return order

    def fill_market(
        self,
        order: Order,
        price: float,
        timestamp=None,
    ) -> Order:
        """Fill a market order at the given price.

        Args:
            order: The order to fill.
            price: The simulated fill price.
            timestamp: Optional fill timestamp.

        Returns:
            The order (now filled).
        """
        if order in self.pending:
            self.pending.remove(order)
        order.status = OrderStatus.FILLED
        order.fill_price = price
        order.filled_at = timestamp
        self.filled.append(order)
        return order

    def should_fill(self, order: Order, high: float, low: float) -> bool:
        """Return True when a pending limit/stop order triggers on a candle.

        A LIMIT BUY fills when low <= limit_price; a LIMIT SELL when
        high >= limit_price. A STOP BUY fills when high >= stop_price; a
        STOP SELL when low <= stop_price. Market orders always trigger.

        Args:
            order: The pending order.
            high: The candle high.
            low: The candle low.

        Returns:
            Whether the order would fill within this candle.
        """
        if order.order_type == OrderType.MARKET:
            return True
        if order.order_type == OrderType.LIMIT:
            limit = order.limit_price if order.limit_price is not None else 0.0
            return (low <= limit) if order.is_buy else (high >= limit)
        if order.order_type == OrderType.STOP:
            stop = order.stop_price if order.stop_price is not None else 0.0
            return (high >= stop) if order.is_buy else (low <= stop)
        return False

    def pending_count(self) -> int:
        """Return the number of pending orders."""
        return len(self.pending)


__all__ = ["OrderManager"]
