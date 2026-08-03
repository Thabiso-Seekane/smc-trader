"""Candle data validation helpers.

This module is responsible for validating OHLCV candle DataFrames
before they are consumed by analysis, backtesting, or execution.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.exceptions import DataValidationError

# Columns required on a valid candle frame.
REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")

# Columns that must hold numeric values.
NUMERIC_COLUMNS = ("open", "high", "low", "close", "volume")


def validate_candles(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate a candle DataFrame.

    Runs a sequence of checks against the supplied DataFrame and raises
    ``DataValidationError`` on the first failing check. The frame is
    returned unchanged when every check passes.

    Checks (in evaluation order):

        * Empty DataFrame
        * Required columns present
        * Correct data types (datetime ``date``, numeric OHLCV)
        * Missing / NaN values
        * Duplicate timestamps
        * Ascending timestamps
        * Invalid OHLC values (positive prices, valid high/low bounds)

    Args:
        frame: OHLCV candle data.

    Returns:
        The validated, unchanged frame.

    Raises:
        DataValidationError: if any validation check fails.
    """

    _raise_if_empty(frame)
    _raise_if_missing_columns(frame)
    _raise_on_bad_dtypes(frame)
    _raise_on_missing_values(frame)
    _raise_on_duplicate_timestamps(frame)
    _raise_on_non_ascending_timestamps(frame)
    _raise_on_invalid_ohlc(frame)
    return frame


def _raise_if_empty(frame: pd.DataFrame) -> None:
    """Reject frames that contain no rows."""

    if frame.empty:
        raise DataValidationError("candle DataFrame is empty")


def _raise_if_missing_columns(frame: pd.DataFrame) -> None:
    """Reject frames that are missing any required OHLCV column."""

    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise DataValidationError(
            "candle DataFrame is missing required columns: " + ", ".join(missing)
        )


def _raise_on_bad_dtypes(frame: pd.DataFrame) -> None:
    """Reject frames with incorrect column data types."""

    if not pd.api.types.is_datetime64_any_dtype(frame["date"]):
        raise DataValidationError(
            f"'date' column must be datetime64, got dtype {frame['date'].dtype}"
        )

    non_numeric = [col for col in NUMERIC_COLUMNS if not pd.api.types.is_numeric_dtype(frame[col])]
    if non_numeric:
        raise DataValidationError(
            "non-numeric values found in columns: " + ", ".join(non_numeric)
        )


def _raise_on_missing_values(frame: pd.DataFrame) -> None:
    """Reject frames that contain missing (NaN/None) values."""

    missing = frame[list(REQUIRED_COLUMNS)].isna()
    if missing.any().any():
        affected = missing.any()
        cols = affected.index[affected.values].tolist()
        raise DataValidationError(
            "candle DataFrame contains missing/NaN values in columns: " + ", ".join(cols)
        )


def _raise_on_duplicate_timestamps(frame: pd.DataFrame) -> None:
    """Reject frames that contain duplicate timestamps."""

    if frame["date"].duplicated().any():
        raise DataValidationError("candle DataFrame contains duplicate timestamps")


def _raise_on_non_ascending_timestamps(frame: pd.DataFrame) -> None:
    """Reject frames whose timestamps are not sorted in ascending order."""

    if not frame["date"].is_monotonic_increasing:
        raise DataValidationError("candle timestamps are not in ascending order")


def _raise_on_invalid_ohlc(frame: pd.DataFrame) -> None:
    """Reject frames with non-positive, infinite, or structurally invalid OHLC values."""

    problems: list[str] = []

    ohlc = frame[["open", "high", "low", "close"]]
    if (ohlc <= 0).any(axis=1).any():
        problems.append("non-positive price found")
    if (frame["volume"] < 0).any():
        problems.append("negative volume found")

    nonfinite = ~np.isfinite(frame[list(NUMERIC_COLUMNS)].to_numpy(dtype="float64"))
    if nonfinite.any():
        problems.append("infinite (non-finite) value found")

    if (frame["high"] < frame["low"]).any():
        problems.append("high is below low")
    if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
        problems.append("high is below the open/close range")
    if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
        problems.append("low is above the open/close range")

    if problems:
        raise DataValidationError("invalid OHLC values: " + "; ".join(problems))


__all__ = ["validate_candles", "REQUIRED_COLUMNS", "NUMERIC_COLUMNS"]

