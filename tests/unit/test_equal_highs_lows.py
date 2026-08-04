"""Unit tests for equal-high/low detection."""

from liquidity.enums import LiquidityType
from liquidity.equal_highs import EqualHighDetector
from liquidity.equal_lows import EqualLowDetector
from liquidity.models import LiquidityLevel


def make_level(price, liquidity_type):
    return LiquidityLevel(price=price, liquidity_type=liquidity_type)


def test_detects_equal_highs_cluster():
    levels = [
        make_level(100.0000, LiquidityType.SWING_HIGH),
        make_level(99.9950, LiquidityType.SWING_HIGH),  # within tolerance
        make_level(101.5000, LiquidityType.SWING_HIGH),  # far away
    ]

    clusters = EqualHighDetector(tolerance=0.0002).detect(levels)

    assert len(clusters) == 1
    assert clusters[0].liquidity_type == LiquidityType.EQUAL_HIGHS
    assert clusters[0].size == 2
    assert abs(clusters[0].price - 99.9975) < 1e-6


def test_detects_equal_lows_cluster():
    levels = [
        make_level(50.0000, LiquidityType.SWING_LOW),
        make_level(50.0020, LiquidityType.SWING_LOW),  # within tolerance
        make_level(51.0000, LiquidityType.SWING_LOW),  # far away
    ]

    clusters = EqualLowDetector(tolerance=0.0002).detect(levels)

    assert len(clusters) == 1
    assert clusters[0].liquidity_type == LiquidityType.EQUAL_LOWS
    assert clusters[0].size == 2


def test_ignores_non_swing_levels():
    levels = [
        make_level(100.0, LiquidityType.RANGE_HIGH),
        make_level(100.0, LiquidityType.SWING_HIGH),
    ]

    clusters = EqualHighDetector().detect(levels)
    assert len(clusters) == 0  # only one swing high -> no cluster


def test_single_swing_does_not_form_cluster():
    levels = [make_level(100.0, LiquidityType.SWING_HIGH)]
    assert EqualHighDetector().detect(levels) == []


def test_no_cluster_when_far_apart():
    levels = [
        make_level(100.0, LiquidityType.SWING_HIGH),
        make_level(110.0, LiquidityType.SWING_HIGH),
    ]
    assert EqualHighDetector().detect(levels) == []
