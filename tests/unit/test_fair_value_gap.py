"""Unit tests for the FairValueGap model and FVGDetector."""

from datetime import datetime

import pandas as pd
import pytest

from smart_money.displacement import DisplacementScore
from smart_money.enums import FillStatus, ImbalanceType, OrderBlockType
from smart_money.fair_value_gap import FVGDetector, FairValueGap


def make_candles(rows) -> pd.DataFrame:
    """Build a candle frame from [open, high, low, close, volume] rows."""
    return pd.DataFrame(
        [
            [datetime(2024, 1, 1 + i), *values]
            for i, values in enumerate(rows)
        ],
        columns=["date", "open", "high", "low", "close", "volume"],
    )


def bull_fvg_frame() -> pd.DataFrame:
    """A frame with exactly one bullish FVG (10..15) at middle candle index 1."""
    return make_candles(
        [
            [10, 10, 10, 10, 0],   # 0
            [10, 14, 10, 13, 0],   # 1 (impulse up)
            [15, 15, 15, 15, 0],   # 2 (gap: low=15 > high[0]=10)
            [14, 14, 12, 13, 0],   # 3 (pullback, no new gap)
        ]
    )


def bear_fvg_frame() -> pd.DataFrame:
    """A frame with exactly one bearish FVG (20..25) at middle candle index 1."""
    return make_candles(
        [
            [25, 25, 25, 25, 0],   # 0
            [25, 25, 21, 22, 0],   # 1 (impulse down)
            [20, 20, 20, 20, 0],   # 2 (gap: high=20 < low[0]=25)
            [22, 23, 22, 22, 0],   # 3 (bounce, no new gap)
        ]
    )


def test_fair_value_gap_directional_helpers():
    gap = FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
    )
    assert gap.is_bullish
    assert not gap.is_bearish
    assert gap.midpoint == pytest.approx(1.15)
    assert gap.range == pytest.approx(0.10)
    assert gap.displacement_strength == 0.0


def test_fair_value_gap_defaults():
    gap = FairValueGap(
        direction=OrderBlockType.BEARISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
    )
    assert gap.imbalance_type == ImbalanceType.FAIR_VALUE_GAP
    assert gap.fill_status == FillStatus.OPEN
    assert gap.filled is False
    assert gap.fill_percentage == 0.0
    assert gap.freshness == 100.0
    assert gap.is_active


def test_fair_value_gap_fill_state():
    gap = FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
        filled=True,
        fill_percentage=100.0,
        fill_status=FillStatus.FILLED,
    )
    assert gap.filled
    assert not gap.is_active
    assert not gap.is_partial


def test_fair_value_gap_hash_is_stable():
    gap = FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
    )
    assert hash(gap) == hash(gap.id)


def test_detector_finds_single_bullish_gap():
    detector = FVGDetector(min_displacement=0.0, min_size_atr=0.0)
    gaps = detector.detect(bull_fvg_frame(), timeframe="H1")
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.direction == OrderBlockType.BULLISH
    assert gap.high == pytest.approx(15.0)
    assert gap.low == pytest.approx(10.0)
    assert gap.index == 1
    assert gap.timeframe == "H1"


def test_detector_finds_single_bearish_gap():
    detector = FVGDetector(min_displacement=0.0, min_size_atr=0.0)
    gaps = detector.detect(bear_fvg_frame(), timeframe="H1")
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.direction == OrderBlockType.BEARISH
    assert gap.high == pytest.approx(25.0)
    assert gap.low == pytest.approx(20.0)
    assert gap.index == 1


def test_detector_returns_empty_without_enough_candles():
    detector = FVGDetector()
    small = make_candles([[10, 10, 10, 10, 0], [10, 14, 10, 13, 0]])
    assert detector.detect(small) == []


def test_detector_returns_empty_on_empty_frame():
    detector = FVGDetector()
    assert detector.detect(pd.DataFrame()) == []


def test_detector_displacement_gate_rejects_high_threshold():
    detector = FVGDetector(min_displacement=1e9, min_size_atr=0.0)
    assert detector.detect(bull_fvg_frame()) == []


def test_detector_requires_confirmed_when_set():
    detector = FVGDetector(
        min_displacement=0.0, min_size_atr=0.0, require_confirmed=True
    )
    gaps = detector.detect(bull_fvg_frame())
    for gap in gaps:
        assert isinstance(gap.displacement, DisplacementScore)


def test_no_gap_when_no_imbalance():
    frame = make_candles(
        [
            [10, 12, 9, 11, 0],
            [11, 13, 10, 12, 0],
            [12, 14, 11, 13, 0],
            [13, 15, 12, 14, 0],
        ]
    )
    detector = FVGDetector(min_displacement=0.0, min_size_atr=0.0)
    assert detector.detect(frame) == []


def test_positions_are_consistently_ordered():
    # Every candle must satisfy low <= open <= high and low <= close <= high.
    frame = pd.concat([bull_fvg_frame(), bear_fvg_frame()])
    assert (frame["low"] <= frame["open"]).all()
    assert (frame["open"] <= frame["high"]).all()
    assert (frame["low"] <= frame["close"]).all()
    assert (frame["close"] <= frame["high"]).all()
