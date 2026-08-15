"""Virtual account valuation and paper position lifecycle accounting."""

from __future__ import annotations

from datetime import datetime

from execution.enums import CloseReason, ExecutionStatus, OrderSide
from execution.models import PaperAccount, PaperPosition, Tick


class PaperPortfolio:
    def __init__(self, account: PaperAccount, contract_size: float = 1.0) -> None:
        self.account = account
        self.contract_size = contract_size

    def unrealized_pnl(self, position: PaperPosition, tick: Tick) -> float:
        price = tick.bid if position.side == OrderSide.BUY else tick.ask
        delta = price - position.entry_price if position.side == OrderSide.BUY else position.entry_price - price
        return delta * position.volume * self.contract_size - position.commission - position.slippage_cost

    def mark_to_market(self, positions: list[PaperPosition], ticks: dict[str, Tick]) -> PaperAccount:
        open_pnl = sum(self.unrealized_pnl(position, ticks[position.symbol]) for position in positions if position.is_open and position.symbol in ticks)
        self.account.equity = self.account.balance + open_pnl
        self.account.peak_equity = max(self.account.peak_equity, self.account.equity)
        self.account.free_margin = self.account.equity - self.account.margin
        self.account.updated_at = datetime.now(self.account.updated_at.tzinfo)
        return self.account

    def close(self, position: PaperPosition, tick: Tick, reason: CloseReason) -> PaperPosition:
        exit_price = position.stop_loss if reason == CloseReason.STOP_LOSS else position.take_profit if reason == CloseReason.TAKE_PROFIT else (tick.bid if position.side == OrderSide.BUY else tick.ask)
        delta = exit_price - position.entry_price if position.side == OrderSide.BUY else position.entry_price - exit_price
        position.exit_price = exit_price
        position.realized_pnl = delta * position.volume * self.contract_size - position.commission - position.slippage_cost
        position.close_reason = reason
        position.closed_at = tick.timestamp
        position.status = ExecutionStatus.CLOSED
        self.account.balance += position.realized_pnl
        self.account.daily_realized_pnl += position.realized_pnl
        self.account.equity = self.account.balance
        self.account.peak_equity = max(self.account.peak_equity, self.account.equity)
        self.account.updated_at = tick.timestamp
        return position


__all__ = ["PaperPortfolio"]
