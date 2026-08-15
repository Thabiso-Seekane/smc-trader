"""Safe adapter from Week 8 TradePlan to a paper-only broker order."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from loguru import logger

from execution.enums import ExecutionStatus, OrderSide, TradingMode
from execution.models import ExecutionResult, PaperOrder
from execution.paper_broker import PaperBroker
from execution.session import SessionFilter
from risk.models import TradePlan


@dataclass(slots=True)
class PaperExecutionConfig:
    mode: TradingMode = TradingMode.PAPER
    strategy_id: str = "smc_v1"
    magic_number: int = 501001
    max_open_trades: int = 3
    max_daily_loss_percent: float = 3.0
    max_spread_points: float = 30.0
    session_filter: SessionFilter = field(default_factory=SessionFilter)

    @classmethod
    def from_settings(cls, settings) -> "PaperExecutionConfig":
        """Build executor guardrails from application settings."""

        requested_mode = str(getattr(settings, "trading_mode", "paper")).lower()
        mode = TradingMode.LIVE if requested_mode == TradingMode.LIVE.value else TradingMode.PAPER
        return cls(
            mode=mode,
            strategy_id=getattr(settings, "execution_strategy_id", "smc_v1"),
            magic_number=getattr(settings, "execution_magic_number", 501001),
            max_open_trades=getattr(settings, "max_open_trades", 3),
            max_daily_loss_percent=getattr(settings, "maximum_daily_loss_percent", 3.0),
            max_spread_points=getattr(settings, "max_spread_points", 30.0),
        )


class PaperExecutor:
    def __init__(self, broker: PaperBroker, config: PaperExecutionConfig | None = None) -> None:
        self.broker = broker
        self.config = config or self._default_config()

    def execute(self, trade_plan: TradePlan, signal_id: str, reason: str = "") -> ExecutionResult:
        side = OrderSide.BUY if trade_plan.is_buy else OrderSide.SELL
        order = PaperOrder(
            trade_id=self._trade_id(), signal_id=signal_id, strategy_id=self.config.strategy_id,
            magic_number=self.config.magic_number, symbol=trade_plan.symbol, timeframe=trade_plan.timeframe,
            side=side, volume=trade_plan.position_size.lots, requested_price=trade_plan.entry_price,
            stop_loss=trade_plan.stop_loss, take_profit=trade_plan.take_profit,
            confluence=trade_plan.confidence, reason=reason or trade_plan.note,
        )
        rejection = self._rejection_reason(trade_plan, signal_id)
        if rejection:
            order.status = ExecutionStatus.REJECTED
            order.rejection_reason = rejection
            self.broker.store.save_order(order)
            logger.warning(
                "TRADE_REJECTED reason={} symbol={} signal_id={} strategy={}",
                rejection, order.symbol, signal_id, order.strategy_id,
            )
            return ExecutionResult(order=order)
        order.status = ExecutionStatus.VALIDATED
        self.broker.store.save_order(order)
        self.broker.store.record_signal(signal_id, order.created_at)
        position = self.broker.submit_order(order)
        position.risk_amount = trade_plan.risk_metrics.risk_amount
        self.broker.store.save_position(position)
        return ExecutionResult(order=order, position=position)

    def _rejection_reason(self, plan: TradePlan, signal_id: str) -> str:
        if self.config.mode != TradingMode.PAPER:
            return "Live execution is disabled; Week 11 is paper-only"
        if not plan.is_ready or plan.is_expired or not plan.is_risk_valid:
            return "Trade plan is not ready for execution"
        if self.broker.store.signal_seen(signal_id):
            return "Duplicate signal"
        if len(self.broker.get_positions()) >= self.config.max_open_trades:
            return "Maximum open positions reached"
        account = self.broker.get_account()
        if account.daily_realized_pnl <= -(account.initial_balance * self.config.max_daily_loss_percent / 100):
            return "Maximum daily loss reached"
        tick = self.broker.get_tick(plan.symbol)
        if tick is None:
            return "No tick data available"
        point = self.broker.get_symbol(plan.symbol).point
        if point <= 0 or tick.spread / point > self.config.max_spread_points:
            return "Spread too high or unavailable"
        if not self.config.session_filter.allows(tick.timestamp):
            return "Outside configured trading session"
        return ""

    def _trade_id(self) -> str:
        now = datetime.now(timezone.utc)
        return f"SMC-{now:%Y%m%d}-{len(self.broker.get_orders()) + 1:04d}"

    def _default_config(self) -> PaperExecutionConfig:
        try:
            from config.settings import get_settings

            return PaperExecutionConfig.from_settings(get_settings())
        except Exception:
            return PaperExecutionConfig()


__all__ = ["PaperExecutionConfig", "PaperExecutor"]
