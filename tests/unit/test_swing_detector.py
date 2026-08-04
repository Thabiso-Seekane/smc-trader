"""Unit tests for the swing detector using synthetic, deterministic data."""

import pandas as pd
import pytest

from structure.enums import SwingType
from structure.swing_detector import SwingDetector
from structure.models import Swing


def make_frame(prices):
    """Build a synthetic OHLC frame from a list of close prices.

    Each bar uses the same price for open/high/low/close so the swing
    detection is fully deterministic on the supplied price series.
    """
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                pd.date_range("2024-01-01", periods=len(prices), freq="5min")
            ),
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [100] * len(prices),
        }
    )


def test_detects_known_swing_highs_and_lows():
    # price series:  100 101 102 101 99 103 104 103 102
    # swings:              ^2        ^4        ^6
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)

    detector = SwingDetector(lookback=2)
    swings = detector.detect(frame)

    highs = [s.index for s in swings if s.is_high]
    lows = [s.index for s in swings if not s.is_high]

    assert highs == [2, 6]
    assert lows == [4]


def test_detected_swing_prices_match_series():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)

    swings = SwingDetector(lookback=2).detect(frame)

    by_index = {s.index: s for s in swings}
    assert by_index[2].price == 102.0
    assert by_index[4].price == 99.0
    assert by_index[6].price == 104.0


def test_swing_type_enum():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    swings = SwingDetector(lookback=2).detect(make_frame(prices))

    highs = [s for s in swings if s.is_high]
    lows = [s for s in swings if not s.is_high]

    assert highs[0].swing_type == SwingType.HIGH
    assert highs[1].swing_type == SwingType.HIGH
    assert lows[0].swing_type == SwingType.LOW


def test_empty_frame_returns_no_swings():
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    assert SwingDetector().detect(empty) == []


def test_short_frame_returns_no_swings():
    # fewer than 2*lookback + 1 bars -> no fractal can be confirmed
    frame = make_frame([100, 101, 102])
    assert SwingDetector().detect(frame) == []


def test_flat_series_returns_no_swings():
    # all prices identical -> no strict fractal high/low
    frame = make_frame([100, 100, 100, 100, 100, 100, 100, 100, 100])
    assert SwingDetector().detect(frame) == []


def test_custom_lookback():
    # a wider lookback window smooths out smaller swings
    prices = [100, 103, 101, 104, 102, 105, 103, 100]
    frame = make_frame(prices)

    swings = SwingDetector(lookback=3).detect(frame)
    indices = [s.index for s in swings]

    assert 104 not in indices  # not a swing at wider lookback


def test_score_swing_measures_distance_from_close():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)

    detector = SwingDetector()
    swing = Swing(index=2, timestamp=frame["date"].iloc[2], price=102.0, is_high=True)
    # close at index 2 equals price (102) -> score 0
    assert detector.score_swing(swing, frame) == 0.0
