"""Enums for the Week 9 Backtesting Engine.

This module contains only enum definitions. It holds no business logic.
"""

from __future__ import annotations

from enum import Enum


class OrderType(str, Enum):
    """Type of order placed by the backtester.

    * ``MARKET`` — executed immediately at the current price.
    * ``LIMIT`` — executed at or better than a limit price.
    * ``STOP`` — executed once price reaches the stop price.
    """

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(str, Enum):
    """Lifecycle state of an order.

    * ``PENDING`` — created but not yet filled.
    * ``FILLED`` — converted into a position.
    * ``CANCELLED`` — removed before filling.
    * ``REJECTED`` — rejected by the risk / margin rules.
    * ``EXPIRED`` — passed its expiry without filling.
    """

    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionStatus(str, Enum):
    """Lifecycle state of an open position.

    * ``OPEN`` — position is currently held.
    * ``CLOSED`` — position has been fully closed.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Direction(str, Enum):
    """Directional bias of an order / position."""

    BUY = "BUY"
    SELL = "SELL"


class TradeResultType(str, Enum):
    """Final outcome of a closed trade.

    * ``WIN`` — the take-profit was reached.
    * ``LOSS`` — the stop-loss was reached.
    * ``BREAKEVEN`` — the trade closed at roughly +/-0 R.
    * ``NO_TRADE`` — the plan never produced a fill.
    """

    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    NO_TRADE = "NO_TRADE"


class ExitReason(str, Enum):
    """Why a position was closed.

    * ``TAKE_PROFIT`` — the target was hit.
    * ``STOP_LOSS`` — the stop was hit.
    * ``TRAILING_STOP`` — a trailing stop ended the trade.
    * ``TIME_EXIT`` — the position expired by time.
    * ``MANUAL`` — closed by an external signal.
    """

    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    TIME_EXIT = "TIME_EXIT"
    MANUAL = "MANUAL"


class IntrabarResolution(str, Enum):
    """Policy for resolving orders when both SL and TP touch in one candle.

    * ``CONSERVATIVE`` — assume the stop-loss was hit first (worst case).
    * ``OPTIMISTIC`` — assume the take-profit was hit first (best case).
    * ``BAR_CLOSE`` — resolve at the candle close (no intrabar detail).
    """

    CONSERVATIVE = "CONSERVATIVE"
    OPTIMISTIC = "OPTIMISTIC"
    BAR_CLOSE = "BAR_CLOSE"


class BacktestStatus(str, Enum):
    """Overall status of a completed backtest."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


__all__ = [
    "OrderType",
    "OrderStatus",
    "PositionStatus",
    "Direction",
    "TradeResultType",
    "ExitReason",
    "IntrabarResolution",
    "BacktestStatus",
]
