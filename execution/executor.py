"""Execution service boundary for paper executors."""
from typing import Protocol
from risk.models import TradePlan

class Executor(Protocol):
    def execute(self, trade_plan: TradePlan, signal_id: str, reason: str = ""): ...

__all__ = ["Executor"]
