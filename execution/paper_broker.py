"""Paper broker that fills virtual market orders and monitors SL/TP."""

from __future__ import annotations

from execution.enums import CloseReason, ExecutionStatus, OrderSide
from execution.models import PaperAccount, PaperFill, PaperOrder, PaperPosition, PaperTrade, SymbolInfo, Tick
from execution.paper_portfolio import PaperPortfolio
from execution.persistence import PaperStore


class PaperBroker:
    """A broker implementation with no MT5 order-send capability."""

    def __init__(self, store: PaperStore, initial_balance: float = 10_000.0, commission_per_lot: float = 0.0, slippage: float = 0.0) -> None:
        self.store = store
        self.account = store.load_account(PaperAccount(initial_balance=initial_balance, balance=initial_balance, equity=initial_balance, free_margin=initial_balance, peak_equity=initial_balance))
        self.commission_per_lot = commission_per_lot
        self.slippage = slippage
        self._ticks: dict[str, Tick] = {}
        self._symbols: dict[str, SymbolInfo] = {}

    def set_symbol(self, info: SymbolInfo) -> None:
        self._symbols[info.symbol] = info

    def set_tick(self, tick: Tick) -> list[PaperPosition]:
        self.account.roll_daily_pnl(tick.timestamp)
        self._ticks[tick.symbol] = tick
        closed = self.monitor_positions(tick)
        self._portfolio(tick.symbol).mark_to_market(self.get_positions(), self._ticks)
        self.store.save_account(self.account)
        return closed

    def get_account(self) -> PaperAccount:
        return self.account

    def get_symbol(self, symbol: str) -> SymbolInfo:
        return self._symbols.get(symbol, SymbolInfo(symbol=symbol))

    def get_tick(self, symbol: str) -> Tick | None:
        return self._ticks.get(symbol)

    def get_positions(self) -> list[PaperPosition]:
        return [position for position in self.store.positions() if position.is_open]

    def get_closed_positions(self) -> list[PaperPosition]:
        return [position for position in self.store.positions() if not position.is_open]

    def get_orders(self) -> list[PaperOrder]:
        return self.store.orders()

    def get_fills(self) -> list[PaperFill]:
        return self.store.fills()

    def get_trades(self) -> list[PaperTrade]:
        return self.store.trades()

    def unrealized_pnl(self, position: PaperPosition) -> float:
        tick = self.get_tick(position.symbol)
        return self._portfolio(position.symbol).unrealized_pnl(position, tick) if tick else 0.0

    def submit_order(self, order: PaperOrder) -> PaperPosition:
        tick = self.get_tick(order.symbol)
        if tick is None:
            order.status = ExecutionStatus.REJECTED
            order.rejection_reason = "No tick data available"
            self.store.save_order(order)
            raise RuntimeError(order.rejection_reason)
        order.status = ExecutionStatus.SUBMITTED
        self.store.save_order(order)
        fill = tick.ask + self.slippage if order.side == OrderSide.BUY else tick.bid - self.slippage
        order.status = ExecutionStatus.FILLED
        order.fill_price = fill
        order.filled_at = tick.timestamp
        self.store.save_order(order)
        position = PaperPosition(
            trade_id=order.trade_id, signal_id=order.signal_id, strategy_id=order.strategy_id,
            magic_number=order.magic_number, symbol=order.symbol, timeframe=order.timeframe,
            side=order.side, volume=order.volume, entry_price=fill, stop_loss=order.stop_loss,
            take_profit=order.take_profit, risk_amount=0.0, confluence=order.confluence,
            reason=order.reason, commission=self.commission_per_lot * order.volume,
            slippage_cost=abs(self.slippage) * order.volume,
        )
        self.store.save_fill(PaperFill(
            fill_id=f"{order.trade_id}:OPEN", trade_id=order.trade_id,
            symbol=order.symbol, side=order.side, volume=order.volume,
            price=fill, commission=position.commission,
            slippage_cost=position.slippage_cost, filled_at=tick.timestamp,
        ))
        self.store.save_position(position)
        return position

    def monitor_positions(self, tick: Tick) -> list[PaperPosition]:
        closed: list[PaperPosition] = []
        portfolio = self._portfolio(tick.symbol)
        for position in self.get_positions():
            if position.symbol != tick.symbol:
                continue
            reason = None
            if position.side == OrderSide.BUY:
                reason = CloseReason.STOP_LOSS if tick.bid <= position.stop_loss else CloseReason.TAKE_PROFIT if tick.bid >= position.take_profit else None
            else:
                reason = CloseReason.STOP_LOSS if tick.ask >= position.stop_loss else CloseReason.TAKE_PROFIT if tick.ask <= position.take_profit else None
            if reason:
                closed.append(portfolio.close(position, tick, reason))
                self.store.save_position(position)
                self._save_closed_trade(position)
        return closed

    def close_position(self, trade_id: str) -> PaperPosition:
        position = next((item for item in self.get_positions() if item.trade_id == trade_id), None)
        if position is None:
            raise KeyError(f"No open paper position {trade_id}")
        tick = self.get_tick(position.symbol)
        if tick is None:
            raise RuntimeError("No tick data available")
        closed = self._portfolio(position.symbol).close(position, tick, CloseReason.MANUAL)
        self.store.save_position(closed)
        self._save_closed_trade(closed)
        self.store.save_account(self.account)
        return closed

    def _save_closed_trade(self, position: PaperPosition) -> None:
        self.store.save_trade(PaperTrade(
            trade_id=position.trade_id, symbol=position.symbol,
            side=position.side, volume=position.volume,
            entry_price=position.entry_price,
            exit_price=float(position.exit_price),
            realized_pnl=position.realized_pnl,
            close_reason=position.close_reason,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
        ))

    def _portfolio(self, symbol: str) -> PaperPortfolio:
        return PaperPortfolio(self.account, self.get_symbol(symbol).contract_size)


__all__ = ["PaperBroker"]
