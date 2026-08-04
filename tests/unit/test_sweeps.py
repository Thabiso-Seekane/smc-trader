"""Unit tests for sweep detection."""

import pandas as pd

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityLevel
from liquidity.sweeps import SweepDetector


def make_level(price, liquidity_type):
    return LiquidityLevel(price=price, liquidity_type=liquidity_type)


def make_frame(highs, lows):
    return pd.DataFrame(
        {
            "date": pd.to_datetime(pd.date_range("2024-01-01", periods=len(highs), freq="5min")),
            "open": highs,
            "high": highs,
            "low": lows,
            "close": highs,
            "volume": [100] * len(highs),
        }
    )


def test_buy_side_swept_when_high_breaks_above():
    level = make_level(100.0, LiquidityType.SWING_HIGH)  # BSL
    frame = make_frame(highs=[101.0, 102.0], lows=[99.0, 99.5])  # high > 100

    SweepDetector().detect([level], frame)
    assert level.swept is True


def test_sell_side_swept_when_low_breaks_below():
    level = make_level(50.0, LiquidityType.SWING_LOW)  # SSL
    frame = make_frame(highs=[51.0, 52.0], lows=[49.0, 49.5])  # low < 50

    SweepDetector().detect([level], frame)
    assert level.swept is True


def test_buy_side_not_swept_within_range():
    level = make_level(100.0, LiquidityType.SWING_HIGH)
    frame = make_frame(highs=[99.0, 99.5], lows=[98.0, 98.5])  # high never >= 100

    SweepDetector().detect([level], frame)
    assert level.swept is False


def test_sell_side_not_swept_within_range():
    level = make_level(50.0, LiquidityType.SWING_LOW)
    frame = make_frame(highs=[51.0, 52.0], lows=[50.5, 51.0])  # low never <= 50

    SweepDetector().detect([level], frame)
    assert level.swept is False


def test_next_target_returns_nearest_active_level():
    above = make_level(110.0, LiquidityType.SWING_HIGH)
    below = make_level(95.0, LiquidityType.SWING_LOW)
    far = make_level(200.0, LiquidityType.SWING_HIGH)

    target = SweepDetector().next_target([above, below, far], current_price=100.0)
    assert target is below  # closest to 100


def test_next_target_ignores_swept_levels():
    above = make_level(110.0, LiquidityType.SWING_HIGH)
    above.swept = True
    active = make_level(150.0, LiquidityType.SWING_HIGH)

    target = SweepDetector().next_target([above, active], current_price=100.0)
    assert target is active


def test_next_target_none_when_no_active():
    swept = make_level(110.0, LiquidityType.SWING_HIGH)
    swept.swept = True
    assert SweepDetector().next_target([swept], current_price=100.0) is None
