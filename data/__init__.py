"""Data access and ingestion package."""

from data.storage import load_candles, save_candles

__all__ = ["load_candles", "save_candles"]
