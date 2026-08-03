import pandas as pd
import pytest

from core.exceptions import DataValidationError
from data.validator import validate_candles


def make_frame(**overrides):
    data = {
        "date": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 00:05"]),
        "open": [1.1000, 1.1010],
        "high": [1.1050, 1.1060],
        "low": [1.0950, 1.0960],
        "close": [1.1025, 1.1035],
        "volume": [100, 110],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_valid_frame_passes_validation():
    frame = make_frame()

    assert validate_candles(frame) is frame


def test_invalid_frame_raises_validation_error():
    frame = make_frame()
    frame.loc[0, "close"] = float("nan")

    with pytest.raises(DataValidationError):
        validate_candles(frame)
