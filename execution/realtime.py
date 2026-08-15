"""Fail-closed orchestration: evaluate Weeks 2-8 only after a candle closes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

import pandas as pd

from execution.market_data import ClosedCandleDetector
from execution.models import EngineHealth
from execution.paper_broker import PaperBroker
from execution.paper_executor import PaperExecutor


@dataclass(slots=True)
class RealTimePaperEngine:
    """Coordinates injected analysis/risk services; errors never create a trade."""

    broker: PaperBroker
    executor: PaperExecutor
    analyze: Callable[[pd.DataFrame], object]
    plan: Callable[[object], object]
    detector: ClosedCandleDetector = field(default_factory=ClosedCandleDetector)
    health: EngineHealth = field(default_factory=lambda: EngineHealth(running=True, healthy=False))

    def on_market(self, symbol: str, timeframe: str, candles: pd.DataFrame, tick) -> object | None:
        try:
            self.broker.set_tick(tick)
            self.health.last_tick_at = tick.timestamp
            closed = self.detector.new_closed_candle(candles)
            if closed is None:
                self.health.healthy = True
                return None
            self.health.last_candle_at = self.detector.last_closed_at
            analysis = self.analyze(candles.iloc[:-1])
            self.health.last_analysis_at = datetime.now(timezone.utc)
            trade_plan = self.plan(analysis)
            if trade_plan is None:
                self.health.healthy = True
                return None
            direction = getattr(trade_plan, "direction", "")
            setup_id = getattr(getattr(analysis, "best", None), "id", "setup")
            signal_id = f"{symbol}:{timeframe}:{self.detector.last_closed_at.isoformat()}:{direction}:{setup_id}"
            result = self.executor.execute(
                trade_plan,
                signal_id,
                getattr(getattr(analysis, "decision", None), "reason", ""),
            )
            self.health.healthy = True
            return result
        except Exception as exc:  # fail closed: capture health and do not retry an order
            self.health.healthy = False
            self.health.error = str(exc)
            return None


__all__ = ["RealTimePaperEngine"]
