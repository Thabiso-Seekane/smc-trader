"""Data download and transformation helpers.

This module is responsible only for fetching candle data from MT5 and
converting it into a pandas DataFrame.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data.mt5_client import get_rates as get_mt5_rates
from data.mt5_client import symbol_info as get_mt5_symbol_info


def download_candles(symbol: str, timeframe: str | None = None, count: int | None = None) -> pd.DataFrame:
    """Request candle data from MT5 and transform it into a DataFrame."""

    raw_rates = get_mt5_rates(symbol=symbol, timeframe=timeframe, count=count)

    # MetaTrader5 returns a NumPy structured array.  Its truth value is
    # intentionally ambiguous, so never use ``if not raw_rates`` here.
    if raw_rates is None or len(raw_rates) == 0:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "volume", "spread", "real_volume"]
        )

    frame = pd.DataFrame(
        raw_rates,
        columns=["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"],
    )
    frame.rename(
        columns={
            "time": "date",
            "tick_volume": "volume",
        },
        inplace=True,
    )
    frame["date"] = pd.to_datetime(frame["date"], unit="s")
    frame = frame.sort_values("date").reset_index(drop=True)

    try:
        info = get_mt5_symbol_info(symbol)
        if info is not None:
            frame.attrs["contract_size"] = float(getattr(info, "trade_contract_size", 1.0))
            frame.attrs["point"] = float(getattr(info, "point", 0.0))
    except Exception:
        # Offline and injected data sources do not need broker metadata.
        pass

    return frame


__all__ = ["download_candles"]
