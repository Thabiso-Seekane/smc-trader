"""Future broker adapter: exposes MT5 account/data reads, never order submission."""

from __future__ import annotations

from execution.market_data import MT5MarketData
from execution.models import PaperAccount, PaperOrder, PaperPosition, SymbolInfo, Tick


class MT5Broker:
    """Read-only MT5 broker facade reserved for a future explicitly enabled live layer."""

    def __init__(self, market_data: MT5MarketData | None = None) -> None:
        self.market_data = market_data or MT5MarketData()

    def get_account(self) -> PaperAccount:
        raw = self.market_data.client.account_info()
        return PaperAccount(initial_balance=float(raw.balance), balance=float(raw.balance), equity=float(raw.equity), free_margin=float(raw.margin_free), margin=float(raw.margin))

    def get_symbol(self, symbol: str) -> SymbolInfo:
        info = self.market_data.symbol(symbol)
        if info is None:
            raise ValueError(f"Unknown MT5 symbol: {symbol}")
        return info

    def get_tick(self, symbol: str) -> Tick | None:
        return self.market_data.tick(symbol)

    def get_positions(self) -> list[PaperPosition]:
        return []

    def get_orders(self) -> list[PaperOrder]:
        return []


__all__ = ["MT5Broker"]
