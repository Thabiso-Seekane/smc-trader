"""Read-only real-time MT5 market-data adapter and closed-candle detector."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import pandas as pd

from execution.models import SymbolInfo, Tick


@dataclass(slots=True)
class ClosedCandleDetector:
    """Emits a candle timestamp once, never the still-forming last row."""

    last_closed_at: datetime | None = None

    def new_closed_candle(self, candles: pd.DataFrame) -> pd.Series | None:
        if candles is None or len(candles) < 2 or "date" not in candles:
            return None
        candle = candles.iloc[-2]
        timestamp = pd.Timestamp(candle["date"]).to_pydatetime()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if self.last_closed_at is not None and timestamp <= self.last_closed_at:
            return None
        self.last_closed_at = timestamp
        return candle


class MT5MarketData:
    """Data-only interface over ``data.mt5_client``; it never sends orders."""

    def __init__(self, client=None) -> None:
        if client is None:
            from data import mt5_client as client
        self.client = client

    def tick(self, symbol: str) -> Tick | None:
        raw = self.client.get_tick(symbol)
        if raw is None:
            return None
        timestamp = datetime.fromtimestamp(getattr(raw, "time", 0), tz=timezone.utc)
        return Tick(symbol=symbol, bid=float(raw.bid), ask=float(raw.ask), timestamp=timestamp)

    def symbol(self, symbol: str) -> SymbolInfo | None:
        raw = self.client.symbol_info(symbol)
        if raw is None:
            return None
        return SymbolInfo(symbol=symbol, point=float(raw.point), contract_size=float(getattr(raw, "trade_contract_size", 1.0)),
                          volume_min=float(getattr(raw, "volume_min", 0.01)), volume_step=float(getattr(raw, "volume_step", 0.01)))

    def candles(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        rows = self.client.get_rates(symbol, timeframe, count)
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        if "time" in frame:
            # Match the timezone-naive UTC convention used by downloaded and
            # persisted candles throughout the analysis pipeline.
            frame["date"] = pd.to_datetime(frame["time"], unit="s")
        return frame.rename(columns={"tick_volume": "volume"})


__all__ = ["ClosedCandleDetector", "MT5MarketData"]
