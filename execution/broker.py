"""Broker boundary. Strategy and risk code must never call a broker directly."""

from __future__ import annotations

from typing import Protocol

from execution.models import PaperAccount, PaperOrder, PaperPosition, SymbolInfo, Tick


class Broker(Protocol):
    def get_account(self) -> PaperAccount: ...
    def get_symbol(self, symbol: str) -> SymbolInfo: ...
    def get_tick(self, symbol: str) -> Tick | None: ...
    def get_positions(self) -> list[PaperPosition]: ...
    def get_orders(self) -> list[PaperOrder]: ...


__all__ = ["Broker"]
