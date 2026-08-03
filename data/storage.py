"""Helpers for persisting and loading candle data as parquet files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _storage_root(root_dir: str | Path | None = None) -> Path:
    """Resolve the root directory used for persisted candle data."""

    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent
    return Path(root_dir) / "data_store"


def save_candles(
    frame: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    date: str,
    root_dir: str | Path | None = None,
) -> Path:
    """Persist a DataFrame to parquet using the project storage layout."""

    target_dir = _storage_root(root_dir) / symbol / timeframe
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{date}.parquet"
    frame.to_parquet(target_path, index=False)
    return target_path


def load_candles(
    *,
    symbol: str,
    timeframe: str,
    date: str,
    root_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Load a candle DataFrame from parquet if it exists."""

    target_path = _storage_root(root_dir) / symbol / timeframe / f"{date}.parquet"
    if not target_path.exists():
        return pd.DataFrame()

    return pd.read_parquet(target_path)


__all__ = ["save_candles", "load_candles"]
