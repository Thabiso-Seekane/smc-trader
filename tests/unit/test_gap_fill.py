"""Unit tests for the FillDetector (fill percentage / status / freshness)."""

from datetime import datetime

import pandas as pd
import pytest

from smart_money.enums import FillStatus, OrderBlockType
from smart_money.fair_value_gap import FairValueGap
from smart_money.fills import FillDetector


def make_candles(rows) -> pd.DataFrame:
    """Build a candle frame from [open, high, low, close, volume] rows."""
    return pd.DataFrame(
        [
            [datetime(2024, 1, 1 + i), *values]
            for i, values in enumerate(rows)
        ],
        columns=["date", "open", "high", "low", "close", "volume"],
    )


def make_gap(direction=OrderBlockType.BULLISH, high=15.0, low=10.0, index=0):
    return FairValueGap(
        direction=direction,
        high=high,
        low=low,
        index=index,
        timestamp=datetime(2024, 1, 1),
    )


def test_open_gap_not_touched():
    # Bullish gap (10..15) at index 0; price continues up, never returns.
    candles = make_candles(
        [
            [10, 15, 10, 10, 0],   # 0 gap origin (high=15 marks the gap top)
            [16, 20, 16, 19, 0],   # 1 continues up, low=16 (above gap)
            [19, 25, 19, 24, 0],   # 2
        ]
    )
    gap = make_gap(index=0)
    detector = FillDetector()
    detector.analyze([gap], candles)
    assert gap.fill_percentage == 0.0
    assert gap.fill_status == FillStatus.OPEN
    assert gap.filled is False
    assert gap.touch_count == 0
    assert gap.freshness == 100.0


def test_partial_fill_down_into_bullish_gap():
    # Bullish gap (10..15); candle 1 trades down to 12 (mid gap) then back up.
    candles = make_candles(
        [
            [10, 15, 10, 10, 0],   # 0 gap origin
            [15, 16, 12, 14, 0],   # 1 enters gap to 12 (low=12)
            [14, 18, 14, 17, 0],   # 2 back up (still above 10)
        ]
    )
    gap = make_gap(index=0)
    detector = FillDetector()
    detector.analyze([gap], candles)
    assert 0.0 < gap.fill_percentage < 100.0
    assert gap.fill_status == FillStatus.PARTIAL
    assert gap.touch_count >= 1
    assert gap.freshness < 100.0


def test_full_fill_through_bullish_gap():
    # Bullish gap (10..15); candle 1 trades down through 10 => 100% fill.
    candles = make_candles(
        [
            [10, 15, 10, 10, 0],   # 0 gap origin
            [12, 12, 8, 9, 0],     # 1 fills through gap fully (low=8)
        ]
    )
    gap = make_gap(index=0)
    detector = FillDetector()
    detector.analyze([gap], candles)
    assert gap.fill_percentage == pytest.approx(100.0)
    assert gap.fill_status == FillStatus.FILLED
    assert gap.filled is True
    assert gap.freshness == 0.0


def test_full_fill_up_into_bearish_gap():
    # Bearish gap (20..25) at index 0; candle 1 trades up through 25 => 100%.
    candles = make_candles(
        [
            [25, 25, 20, 25, 0],   # 0 gap origin (low=20 marks gap bottom)
            [21, 27, 21, 26, 0],   # 1 fills up through gap (high=27)
        ]
    )
    gap = make_gap(direction=OrderBlockType.BEARISH, high=25.0, low=20.0, index=0)
    detector = FillDetector()
    detector.analyze([gap], candles)
    assert gap.fill_percentage == pytest.approx(100.0)
    assert gap.filled is True


def test_returns_empty_on_empty_frame():
    detector = FillDetector()
    detector.analyze([], pd.DataFrame())
    assert True  # no crash
