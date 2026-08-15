"""Position management for the Week 9 Backtesting Engine.

The ``PositionManager`` opens positions from filled orders and closes them
when the stop-loss or take-profit is touched. It tracks MFE / MAE and
computes the realized P&L (including commission and slippage).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtesting.commission import CommissionModel
from backtesting.enums import Direction, ExitReason, PositionStatus, TradeResultType
from backtesting.models import Position, Trade
from backtesting.slippage import SlippageModel


@dataclass(slots=True)
class PositionManager:
    """Opens and closes positions, tracking MFE/MAE and realized P&L.

    Attributes:
        commission: The :class:`CommissionModel` to apply.
        slippage: The :class:`SlippageModel` to apply on entry/exit.
        open_positions: Currently held positions.
        closed_positions: Positions that have been closed.
        trades: Realized :class:`Trade` records.
    """

    commission: CommissionModel = field(default_factory=CommissionModel)
    slippage: SlippageModel = field(default_factory=SlippageModel)
    contract_size: float = 1.0
    open_positions: list[Position] = field(default_factory=list)
    closed_positions: list[Position] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)

    def open_position(
        self,
        order,
        price: float,
        stop_loss: float,
        take_profit: float,
        risk_amount: float,
        timestamp: datetime | None = None,
        confluence_score: float = 0.0,
        reason: str = "",
    ) -> Position:
        """Open a position from a filled order.

        Args:
            order: The filled order.
            price: The simulated entry price (pre-slippage).
            stop_loss: The protective stop-loss price.
            take_profit: The take-profit price.
            risk_amount: Currency risked on the position.
            timestamp: Optional entry timestamp.
            confluence_score: Week 7 confluence of the setup.
            reason: Attribution string.

        Returns:
            The newly opened :class:`Position`.
        """
        entry_price = self.slippage.apply(price, order.direction)
        pos = Position(
            symbol=order.symbol,
            direction=order.direction,
            entry_price=entry_price,
            volume=order.volume,
            contract_size=self.contract_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=timestamp or datetime.now(),
            risk_amount=risk_amount,
            status=PositionStatus.OPEN,
            confluence_score=confluence_score,
            reason=reason,
        )
        pos.slippage_cost = abs(entry_price - price) * order.volume * self.contract_size
        self.open_positions.append(pos)
        return pos

    def update(self, pos: Position, high: float, low: float) -> None:
        """Update MFE / MAE for an open position given a candle's high/low.

        Args:
            pos: The open position.
            high: The candle high.
            low: The candle low.
        """
        if pos.is_buy:
            pos.mfe = max(pos.mfe, (high - pos.entry_price) * pos.volume * self.contract_size)
            pos.mae = min(pos.mae, (low - pos.entry_price) * pos.volume * self.contract_size)
        else:
            pos.mfe = max(pos.mfe, (pos.entry_price - low) * pos.volume * self.contract_size)
            pos.mae = min(pos.mae, (pos.entry_price - high) * pos.volume * self.contract_size)

    def close_position(
        self,
        pos: Position,
        price: float,
        reason: ExitReason,
        timestamp: datetime | None = None,
    ) -> Trade:
        """Close an open position at a given price.

        Args:
            pos: The position to close.
            price: The simulated exit price (pre-slippage).
            reason: Why the position is being closed.
            timestamp: Optional exit timestamp.

        Returns:
            The realized :class:`Trade` record.
        """
        exit_price = self.slippage.apply(price, _exit_direction(pos.direction))
        raw_pnl = self._raw_pnl(pos, exit_price)
        commission = self.commission.charge(pos.volume)
        pos.exit_price = exit_price
        pos.exit_time = timestamp
        pos.exit_reason = reason
        pos.commission = commission
        pos.slippage_cost += abs(exit_price - price) * pos.volume * self.contract_size
        pos.profit_loss = raw_pnl - commission
        pos.status = PositionStatus.CLOSED

        if pos in self.open_positions:
            self.open_positions.remove(pos)
        self.closed_positions.append(pos)

        trade = Trade(
            symbol=pos.symbol,
            direction=pos.direction,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            volume=pos.volume,
            entry_time=pos.entry_time,
            exit_time=timestamp or pos.exit_time or datetime.now(),
            risk_amount=pos.risk_amount,
            profit_loss=pos.profit_loss,
            commission=commission,
            slippage_cost=pos.slippage_cost,
            exit_reason=reason,
            result=self._classify(pos.profit_loss),
            r_multiple=pos.r_multiple,
            confluence_score=pos.confluence_score,
            reason=pos.reason,
        )
        self.trades.append(trade)
        return trade

    def _raw_pnl(self, pos: Position, exit_price: float) -> float:
        """Return the raw P&L (before commission) at an exit price."""
        if pos.is_buy:
            return (exit_price - pos.entry_price) * pos.volume * pos.contract_size
        return (pos.entry_price - exit_price) * pos.volume * pos.contract_size

    @staticmethod
    def _classify(pnl: float) -> TradeResultType:
        """Classify a realized P&L into WIN / LOSS / BREAKEVEN."""
        if pnl > 0:
            return TradeResultType.WIN
        if pnl < 0:
            return TradeResultType.LOSS
        return TradeResultType.BREAKEVEN


def _exit_direction(direction: Direction) -> Direction:
    """For exit slippage, a long closes like a sell and vice-versa."""
    return Direction.SELL if direction == Direction.BUY else Direction.BUY


__all__ = ["PositionManager"]
