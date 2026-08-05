"""Unit tests for equal-lows detection."""

from liquidity.enums import LiquidityType
from liquidity.equal_lows import EqualLowDetector
from liquidity.models import LiquidityLevel


def make_level(price, liquidity_type):
    return LiquidityLevel(price=price, liquidity_type=liquidity_type)


def test_detects_equal_lows_cluster():
    # For USDJPY one pip = 0.01. A diff of 0.01 (1 pip) is within a 2-pip
    # tolerance.
    levels = [
        make_level(150.00, LiquidityType.SWING_LOW),
        make_level(150.01, LiquidityType.SWING_LOW),  # 1 pip apart
        make_level(151.00, LiquidityType.SWING_LOW),  # far away
    ]

    clusters = EqualLowDetector(tolerance=2, symbol="USDJPY").detect(levels)

    assert len(clusters) == 1
    assert clusters[0].liquidity_type == LiquidityType.EQUAL_LOWS
    assert clusters[0].size == 2


def test_tolerance_normalized_by_symbol():
    jpy_levels = [
        make_level(150.00, LiquidityType.SWING_LOW),
        make_level(150.005, LiquidityType.SWING_LOW),
    ]
    eur_levels = [
        make_level(1.25000, LiquidityType.SWING_LOW),
        make_level(1.25500, LiquidityType.SWING_LOW),
    ]

    assert len(EqualLowDetector(tolerance=2, symbol="USDJPY").detect(jpy_levels)) == 1
    assert EqualLowDetector(tolerance=2, symbol="EURUSD").detect(eur_levels) == []


def test_single_swing_does_not_form_cluster():
    levels = [make_level(100.0, LiquidityType.SWING_LOW)]
    assert EqualLowDetector().detect(levels) == []


def test_no_cluster_when_far_apart():
    levels = [
        make_level(100.0, LiquidityType.SWING_LOW),
        make_level(110.0, LiquidityType.SWING_LOW),
    ]
    assert EqualLowDetector().detect(levels) == []
