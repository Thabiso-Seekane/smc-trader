"""Typed records exchanged by the Week 11 paper-trading services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from execution.enums import CloseReason, ExecutionStatus, OrderSide, OrderType, TradingMode


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Tick:
    symbol: str
    bid: float
    ask: float
    timestamp: datetime = field(default_factory=utc_now)

    @property
    def spread(self) -> float:
        return max(0.0, self.ask - self.bid)


@dataclass(slots=True)
class SymbolInfo:
    symbol: str
    point: float = 0.01
    contract_size: float = 1.0
    volume_min: float = 0.01
    volume_step: float = 0.01


@dataclass(slots=True)
class PaperOrder:
    trade_id: str
    signal_id: str
    strategy_id: str
    magic_number: int
    symbol: str
    timeframe: str
    side: OrderSide
    volume: float
    requested_price: float
    stop_loss: float
    take_profit: float
    confluence: float = 0.0
    reason: str = ""
    status: ExecutionStatus = ExecutionStatus.CREATED
    created_at: datetime = field(default_factory=utc_now)
    filled_at: datetime | None = None
    fill_price: float | None = None
    rejection_reason: str = ""
    order_type: OrderType = OrderType.MARKET


@dataclass(slots=True)
class PaperFill:
    fill_id: str
    trade_id: str
    symbol: str
    side: OrderSide
    volume: float
    price: float
    commission: float = 0.0
    slippage_cost: float = 0.0
    filled_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class PaperTrade:
    trade_id: str
    symbol: str
    side: OrderSide
    volume: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    close_reason: CloseReason
    opened_at: datetime
    closed_at: datetime


@dataclass(slots=True)
class PaperPosition:
    trade_id: str
    signal_id: str
    strategy_id: str
    magic_number: int
    symbol: str
    timeframe: str
    side: OrderSide
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    confluence: float = 0.0
    reason: str = ""
    status: ExecutionStatus = ExecutionStatus.FILLED
    opened_at: datetime = field(default_factory=utc_now)
    closed_at: datetime | None = None
    exit_price: float | None = None
    close_reason: CloseReason | None = None
    realized_pnl: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.status == ExecutionStatus.FILLED


@dataclass(slots=True)
class PaperAccount:
    initial_balance: float = 10_000.0
    balance: float = 10_000.0
    equity: float = 10_000.0
    margin: float = 0.0
    free_margin: float = 10_000.0
    peak_equity: float = 10_000.0
    daily_realized_pnl: float = 0.0
    daily_pnl_date: str = field(default_factory=lambda: utc_now().date().isoformat())
    updated_at: datetime = field(default_factory=utc_now)

    @property
    def drawdown_percent(self) -> float:
        return 0.0 if self.peak_equity <= 0 else max(0.0, (self.peak_equity - self.equity) / self.peak_equity * 100)

    @property
    def realized_pnl(self) -> float:
        return self.balance - self.initial_balance

    @property
    def unrealized_pnl(self) -> float:
        return self.equity - self.balance

    def roll_daily_pnl(self, timestamp: datetime) -> None:
        day = timestamp.astimezone(timezone.utc).date().isoformat()
        if day != self.daily_pnl_date:
            self.daily_realized_pnl = 0.0
            self.daily_pnl_date = day


@dataclass(slots=True)
class ExecutionResult:
    order: PaperOrder
    position: PaperPosition | None = None


@dataclass(slots=True)
class EngineHealth:
    running: bool = False
    healthy: bool = False
    last_tick_at: datetime | None = None
    last_candle_at: datetime | None = None
    last_analysis_at: datetime | None = None
    error: str = ""
    mode: TradingMode = TradingMode.PAPER


__all__ = ["Tick", "SymbolInfo", "PaperOrder", "PaperFill", "PaperTrade", "PaperPosition", "PaperAccount", "ExecutionResult", "EngineHealth", "utc_now"]
