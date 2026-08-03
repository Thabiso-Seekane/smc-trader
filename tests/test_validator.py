import pandas as pd
import pytest

from core.exceptions import DataValidationError
from data.validator import validate_candles


def make_frame(**overrides):
    """Build a valid candle DataFrame, optionally overriding values."""
    data = {
        "date": pd.to_datetime(
            ["2024-01-01 00:00", "2024-01-01 00:05", "2024-01-01 00:10", "2024-01-01 00:15"]
        ),
        "open": [1.1000, 1.1010, 1.1020, 1.1030],
        "high": [1.1050, 1.1060, 1.1070, 1.1080],
        "low": [1.0950, 1.0960, 1.0970, 1.0980],
        "close": [1.1025, 1.1035, 1.1045, 1.1055],
        "volume": [100, 110, 120, 130],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_valid_frame_passes_unchanged():
    frame = make_frame()
    assert validate_candles(frame) is frame


def test_empty_frame_raises():
    with pytest.raises(DataValidationError):
        validate_candles(pd.DataFrame())


def test_missing_column_raises():
    with pytest.raises(DataValidationError):
        validate_candles(make_frame().drop(columns=["volume"]))


def test_wrong_date_dtype_raises():
    frame = make_frame()
    frame["date"] = frame["date"].astype(str)
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_non_numeric_price_raises():
    frame = make_frame()
    frame["close"] = frame["close"].astype(str)
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_nan_value_raises():
    frame = make_frame()
    frame.loc[1, "high"] = float("nan")
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_duplicate_timestamps_raise():
    frame = make_frame()
    frame.loc[1, "date"] = frame.loc[0, "date"]
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_non_ascending_timestamps_raise():
    frame = make_frame()
    frame["date"] = frame["date"][::-1].reset_index(drop=True)
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_non_positive_price_raises():
    frame = make_frame()
    frame.loc[2, "open"] = 0.0
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_negative_volume_raises():
    frame = make_frame()
    frame.loc[0, "volume"] = -5
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_high_below_low_raises():
    frame = make_frame()
    frame.loc[0, "high"] = 1.0900  # below low 1.0950
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_high_below_open_close_range_raises():
    frame = make_frame()
    frame.loc[3, "high"] = 1.1020  # below open/close 1.1030/1.1055
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_low_above_open_close_range_raises():
    frame = make_frame()
    frame.loc[3, "low"] = 1.1045  # above open/close 1.1030/1.1055
    with pytest.raises(DataValidationError):
        validate_candles(frame)


def test_infinite_value_raises():
    frame = make_frame()
    frame.loc[0, "close"] = float("inf")
    with pytest.raises(DataValidationError):
        validate_candles(frame)

