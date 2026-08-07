"""Data models for the Week 9 Backtesting Engine.

This module contains only data models (dataclasses) and holds no business
logic. The backtester replays historical OHLC candles sequentially and
simulates orders → positions → trades while tracking a portfolio and
producing performance analytics.

The models here are deliberately typed (no dicts) so the Week 10 dashboard
can consume a :class:`BacktestResult` object directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from backtesting.enums import (
    Direction,
    ExitReason,
    OrderStatus,
    OrderType,
    PositionStatus,
    TradeResultType,
)


@dataclass(slots=True)
class BacktestConfig:
    """Configuration for a single backtest run.

    Attributes:
        initial_balance: Starting cash balance.
        commission: Commission per lot (currency units per lot).
        slippage: Fixed slippage in price units applied to fills.
        spread: Bid/ask spread in price units.
        risk_per_trade: Per-trade risk as a fraction of balance (0.01 = 1%).
        intrabar_resolution: How to resolve when both SL and TP touch in
            one candle.
        symbol: Symbol label attached to the run.
        timeframe: Timeframe label attached to the run.
    """

    initial_balance: float = 10_000.0
    commission: float = 7.0
    slippage: float = 0.0
    spread: float = 0.0
    risk_per_trade: float = 0.01
    intrabar_resolution: str = "CONSERVATIVE"
    symbol: str = ""
    timeframe: str = ""


@dataclass(slots=True)
class Order:
    """An order to buy or sell.

    An order is distinct from a position: an order is *requested*, and once
    filled it becomes a :class:`Position`.

    Attributes:
        id: Unique identifier.
        symbol: Trading symbol.
        direction: Buy or sell.
        order_type: MARKET / LIMIT / STOP.
        volume: Lot / unit size.
        limit_price: For LIMIT orders (optional).
        stop_price: For STOP orders (optional).
        status: Current order lifecycle state.
        created_at: When the order was created.
        filled_at: When the order was filled (optional).
        fill_price: The actual simulated fill price (optional).
        reason: Human-readable reason behind the order.
    """

    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    direction: Direction = Direction.BUY
    order_type: OrderType = OrderType.MARKET
    volume: float = 0.0
    limit_price: float | None = None
    stop_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: datetime | None = None
    fill_price: float | None = None
    reason: str = ""

    @property
    def is_buy(self) -> bool:
        """Return True when this is a buy order."""
        return self.direction == Direction.BUY

    @property
    def is_sell(self) -> bool:
        """Return True when this is a sell order."""
        return self.direction == Direction.SELL

    @property
    def is_filled(self) -> bool:
        """Return True when the order has been filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_pending(self) -> bool:
        """Return True when the order is still pending."""
        return self.status == OrderStatus.PENDING


@dataclass(slots=True)
class Position:
    """An open position resulting from a filled order.

    Attributes:
        id: Unique identifier.
        symbol: Trading symbol.
        direction: Buy or sell.
        entry_price: Actual simulated entry price.
        volume: Lot / unit size.
        stop_loss: Protective stop-loss price.
        take_profit: Take-profit price.
        entry_time: When the position was opened.
        exit_price: Actual simulated exit price (optional).
        exit_time: When the position was closed (optional).
        exit_reason: How the position was closed (optional).
        risk_amount: Currency risked on the position.
        profit_loss: Realized P&L (after commission/slippage) when closed.
        commission: Total commission charged on open+close.
        slippage_cost: Total slippage impact on open+close.
        status: OPEN or CLOSED.
        mfe: Maximum favourable excursion (best unrealized gain).
        mae: Maximum adverse excursion (worst unrealized loss).
        confluence_score: Week 7 confluence score of the originating setup.
        reason: Human-readable attribution (why the trade happened).
    """

    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    direction: Direction = Direction.BUY
    entry_price: float = 0.0
    volume: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    exit_price: float | None = None
    exit_time: datetime | None = None
    exit_reason: ExitReason | None = None
    risk_amount: float = 0.0
    profit_loss: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    mfe: float = 0.0
    mae: float = 0.0
    confluence_score: float = 0.0
    reason: str = ""

    @property
    def is_buy(self) -> bool:
        """Return True when this is a long position."""
        return self.direction == Direction.BUY

    @property
    def is_sell(self) -> bool:
        """Return True when this is a short position."""
        return self.direction == Direction.SELL

    @property
    def is_open(self) -> bool:
        """Return True while the position is still open."""
        return self.status == PositionStatus.OPEN

    @property
    def is_closed(self) -> bool:
        """Return True once the position has been closed."""
        return self.status == PositionStatus.CLOSED

    @property
    def risk_distance(self) -> float:
        """Return the stop distance in price units."""
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_distance(self) -> float:
        """Return the target distance in price units."""
        return abs(self.take_profit - self.entry_price)

    @property
    def risk_reward(self) -> float:
        """Return the reward-to-risk ratio (0 when risk is zero)."""
        if self.risk_distance <= 0:
            return 0.0
        return self.reward_distance / self.risk_distance

    @property
    def r_multiple(self) -> float:
        """Return the realized R-multiple of the trade.

        R = P&L / risk. A win of +2R yields 2.0; a full loss yields -1.0.
        """
        if self.risk_amount <= 0:
            return 0.0
        return self.profit_loss / self.risk_amount

    def unrealized_pnl(self, price: float) -> float:
        """Return the unrealized P&L at a given price.

        Uses a per-unit price-change × volume model (volume in units).
        """
        if self.is_buy:
            return (price - self.entry_price) * self.volume
        return (self.entry_price - price) * self.volume

    def __hash__(self) -> int:
        """Hash by position identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class Trade:
    """A fully closed trade (the record of a realized position).

    Attributes:
        id: Unique identifier.
        symbol: Trading symbol.
        direction: Buy or sell.
        entry_price: Simulated entry price.
        exit_price: Simulated exit price.
        volume: Lot / unit size.
        entry_time: When the trade opened.
        exit_time: When the trade closed.
        risk_amount: Currency risked.
        profit_loss: Realized P&L (after costs).
        commission: Total commission charged.
        slippage_cost: Total slippage impact.
        exit_reason: How the trade ended.
        result: WIN / LOSS / BREAKEVEN.
        r_multiple: Realized R-multiple.
        confluence_score: Week 7 confluence of the setup.
        reason: Attribution summary.
    """

    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    direction: Direction = Direction.BUY
    entry_price: float = 0.0
    exit_price: float = 0.0
    volume: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: datetime = field(default_factory=datetime.now)
    risk_amount: float = 0.0
    profit_loss: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0
    exit_reason: ExitReason = ExitReason.MANUAL
    result: TradeResultType = TradeResultType.BREAKEVEN
    r_multiple: float = 0.0
    confluence_score: float = 0.0
    reason: str = ""

    @property
    def is_win(self) -> bool:
        """Return True when this trade was a win."""
        return self.result == TradeResultType.WIN

    @property
    def is_loss(self) -> bool:
        """Return True when this trade was a loss."""
        return self.result == TradeResultType.LOSS

    @property
    def is_profitable(self) -> bool:
        """Return True when realized P&L is positive."""
        return self.profit_loss > 0.0

    def __hash__(self) -> int:
        """Hash by trade identity (id)."""
        return hash(self.id)


@dataclass(slots=True)
class EquityPoint:
    """A single point on the portfolio equity curve.

    Attributes:
        timestamp: When this equity snapshot was recorded.
        balance: Realized cash balance at that time.
        equity: Balance + unrealized P&L.
        drawdown: Drawdown from the running equity peak (fraction).
    """

    timestamp: datetime
    balance: float
    equity: float
    drawdown: float = 0.0


@dataclass(slots=True)
class PerformanceSummary:
    """Aggregate performance statistics for a backtest.

    Attributes:
        initial_balance: Starting balance.
        final_balance: Ending balance.
        total_return: Total return (fraction).
        total_trades: Number of closed trades.
        winning_trades: Number of winning trades.
        losing_trades: Number of losing trades.
        win_rate: Fraction of trades that won.
        profit_factor: Gross profit / gross loss.
        max_drawdown: Worst equity drawdown (fraction).
        sharpe_ratio: Annualized Sharpe (from trade returns).
        average_rr: Average R-multiple per trade.
        average_trade: Average P&L per trade.
        largest_win: Largest single-trade profit.
        largest_loss: Largest single-trade loss.
        expectancy: Expected P&L per trade (currency).
        expectancy_r: Expected R per trade.
    """

    initial_balance: float = 0.0
    final_balance: float = 0.0
    total_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    average_rr: float = 0.0
    average_trade: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    expectancy: float = 0.0
    expectancy_r: float = 0.0


@dataclass(slots=True)
class BacktestResult:
    """The complete output of a backtest run.

    Attributes:
        config: The :class:`BacktestConfig` used.
        initial_balance: Starting balance.
        final_balance: Ending balance.
        total_return: Total return (fraction).
        total_trades: Number of closed trades.
        winning_trades: Number of winning trades.
        losing_trades: Number of losing trades.
        win_rate: Fraction of trades that won.
        profit_factor: Gross profit / gross loss.
        max_drawdown: Worst equity drawdown (fraction).
        sharpe_ratio: Annualized Sharpe.
        average_rr: Average R per trade.
        average_trade: Average P&L per trade.
        largest_win: Largest single-trade profit.
        largest_loss: Largest single-trade loss.
        expectancy: Expected P&L per trade.
        equity_curve: List of :class:`EquityPoint`.
        trades: List of closed :class:`Trade`.
        positions: List of all :class:`Position` (open and closed).
        status: Completion status.
    """

    config: BacktestConfig = field(default_factory=BacktestConfig)
    initial_balance: float = 0.0
    final_balance: float = 0.0
    total_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    average_rr: float = 0.0
    average_trade: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    expectancy: float = 0.0
    equity_curve: list[EquityPoint] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    positions: list[Position] = field(default_factory=list)
    status: str = "COMPLETED"

    @property
    def summary(self) -> PerformanceSummary:
        """Return a :class:`PerformanceSummary` mirroring the headline metrics."""
        return PerformanceSummary(
            initial_balance=self.initial_balance,
            final_balance=self.final_balance,
            total_return=self.total_return,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            win_rate=self.win_rate,
            profit_factor=self.profit_factor,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=self.sharpe_ratio,
            average_rr=self.average_rr,
            average_trade=self.average_trade,
            largest_win=self.largest_win,
            largest_loss=self.largest_loss,
            expectancy=self.expectancy,
        )


__all__ = [
    "BacktestConfig",
    "Order",
    "Position",
    "Trade",
    "EquityPoint",
    "PerformanceSummary",
    "BacktestResult",
]
