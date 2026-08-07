"""Event-driven trade simulator for the Week 9 Backtesting Engine.

The ``TradeSimulator`` processes candles **sequentially** — one candle at a
time — and never uses future data. This prevents look-ahead bias.

For each candle it:

    1. Fills any pending limit / stop orders that trigger.
    2. Updates MFE / MAE for open positions.
    3. Resolves stop-loss / take-profit exits (respecting the intrabar
       resolution policy).

Intrabar policy:

    * ``CONSERVATIVE`` — when both SL and TP touch in one candle, assume the
      stop-loss was hit first (worst case).
    * ``OPTIMISTIC`` — assume the take-profit was hit first (best case).
    * ``BAR_CLOSE`` — resolve at the candle close (no intrabar detail).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtesting.enums import ExitReason, IntrabarResolution
from backtesting.models import Position, Trade
from backtesting.orders import OrderManager
from backtesting.position import PositionManager
from backtesting.portfolio import Portfolio


@dataclass(slots=True)
class TradeSimulator:
    """Drives order-filling and position lifecycle per candle.

    Attributes:
        orders: The :class:`OrderManager` tracking order fills.
        positions: The :class:`PositionManager` managing open/close.
        portfolio: The :class:`Portfolio` tracking cash and equity.
        intrabar_resolution: The policy for resolving SL/TP collisions.
    """

    orders: OrderManager = field(default_factory=OrderManager)
    positions: PositionManager = field(default_factory=PositionManager)
    portfolio: Portfolio = field(default_factory=Portfolio)
    intrabar_resolution: str = IntrabarResolution.CONSERVATIVE.value

    def process_candle(
        self,
        high: float,
        low: float,
        close: float,
        timestamp: datetime | None = None,
    ) -> list[Trade]:
        """Process a single candle bar.

        Sequential processing means this method only sees the current bar's
        OHLC — it never looks ahead. It fills pending orders and resolves
        open positions.

        Args:
            high: The candle high.
            low: The candle low.
            close: The candle close.
            timestamp: Optional candle timestamp.

        Returns:
            The list of trades closed during this candle.
        """
        closed: list[Trade] = []

        # 1) Fill any pending orders that trigger within this bar.
        self._fill_pending(high, low, timestamp)

        # 2) Update MFE / MAE for all open positions.
        for pos in list(self.positions.open_positions):
            self.positions.update(pos, high, low)

        # 3) Resolve exits for open positions.
        for pos in list(self.positions.open_positions):
            trade = self._resolve_exit(pos, high, low, close, timestamp)
            if trade is not None:
                closed.append(trade)
                self.portfolio.close_position(pos)

        return closed

    def _fill_pending(
        self,
        high: float,
        low: float,
        timestamp: datetime | None,
    ) -> None:
        """Fill any pending orders that trigger within the current bar."""
        for order in list(self.orders.pending):
            if self.orders.should_fill(order, high, low):
                fill_price = self._trigger_price(order, high, low)
                self.orders.fill_market(order, fill_price, timestamp)

    def _trigger_price(self, order, high: float, low: float) -> float:
        """Determine the fill price for a triggering order."""
        if order.order_type.name == "MARKET":
            return low if order.is_buy else high
        if order.limit_price is not None:
            return order.limit_price
        if order.stop_price is not None:
            return order.stop_price
        return low if order.is_buy else high

    def _resolve_exit(
        self,
        pos: Position,
        high: float,
        low: float,
        close: float,
        timestamp: datetime | None,
    ) -> Trade | None:
        """Resolve whether a position exits on this candle.

        Applies the configured intrabar resolution policy.

        Args:
            pos: The open position.
            high: The candle high.
            low: The candle low.
            close: The candle close.
            timestamp: Optional exit timestamp.

        Returns:
            A :class:`Trade` if the position closed, else ``None``.
        """
        sl_hit = self._sl_hit(pos, low, high)
        tp_hit = self._tp_hit(pos, high, low)

        if sl_hit and tp_hit:
            if (
                self.intrabar_resolution
                == IntrabarResolution.CONSERVATIVE.value
            ):
                return self.positions.close_position(
                    pos, pos.stop_loss, ExitReason.STOP_LOSS, timestamp
                )
            if (
                self.intrabar_resolution
                == IntrabarResolution.OPTIMISTIC.value
            ):
                return self.positions.close_position(
                    pos, pos.take_profit, ExitReason.TAKE_PROFIT, timestamp
                )
            # BAR_CLOSE: resolve at the candle close using the close price.
            return self.positions.close_position(
                pos, close, ExitReason.MANUAL, timestamp
            )

        if sl_hit:
            return self.positions.close_position(
                pos, pos.stop_loss, ExitReason.STOP_LOSS, timestamp
            )

        if tp_hit:
            return self.positions.close_position(
                pos, pos.take_profit, ExitReason.TAKE_PROFIT, timestamp
            )

        return None

    @staticmethod
    def _sl_hit(pos: Position, low: float, high: float) -> bool:
        """Return True when the stop-loss is touched by this candle."""
        if pos.is_buy:
            return low <= pos.stop_loss
        return high >= pos.stop_loss

    @staticmethod
    def _tp_hit(pos: Position, high: float, low: float) -> bool:
        """Return True when the take-profit is touched by this candle."""
        if pos.is_buy:
            return high >= pos.take_profit
        return low <= pos.take_profit


__all__ = ["TradeSimulator"]
