"""Data download and transformation helpers.

This module is responsible only for fetching candle data from MT5 and
converting it into a pandas DataFrame.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data.mt5_client import get_rates as get_mt5_rates


def download_candles(symbol: str, timeframe: str | None = None, count: int | None = None) -> pd.DataFrame:
    """Request candle data from MT5 and transform it into a DataFrame."""

    raw_rates = get_mt5_rates(symbol=symbol, timeframe=timeframe, count=count)

    if not raw_rates:
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

    return frame


__all__ = ["download_candles"]
