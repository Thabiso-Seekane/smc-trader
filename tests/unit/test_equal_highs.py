"""Unit tests for equal-highs detection."""

from liquidity.enums import LiquidityType
from liquidity.equal_highs import EqualHighDetector
from liquidity.models import LiquidityLevel


def make_level(price, liquidity_type):
    return LiquidityLevel(price=price, liquidity_type=liquidity_type)


def test_detects_equal_highs_cluster():
    # For EURUSD one pip = 0.0001. A diff of 0.00003 (0.3 pips) is well
    # within a 2-pip tolerance, so these highs are "equal".
    levels = [
        make_level(1.25002, LiquidityType.SWING_HIGH),
        make_level(1.25005, LiquidityType.SWING_HIGH),  # 0.00003 apart
        make_level(1.26000, LiquidityType.SWING_HIGH),  # far away
    ]

    clusters = EqualHighDetector(tolerance=2, symbol="EURUSD").detect(levels)

    assert len(clusters) == 1
    assert clusters[0].liquidity_type == LiquidityType.EQUAL_HIGHS
    assert clusters[0].size == 2
    assert abs(clusters[0].price - 1.250035) < 1e-6


def test_tolerance_normalized_by_symbol():
    # Same 0.005 price gap. For EURUSD (pip=0.0001) that is 50 pips -> not
    # equal. For USDJPY (pip=0.01) that is 0.5 pips -> equal.
    eur_levels = [
        make_level(1.25000, LiquidityType.SWING_HIGH),
        make_level(1.25500, LiquidityType.SWING_HIGH),
    ]
    jpy_levels = [
        make_level(150.00, LiquidityType.SWING_HIGH),
        make_level(150.005, LiquidityType.SWING_HIGH),
    ]

    assert EqualHighDetector(tolerance=2, symbol="EURUSD").detect(eur_levels) == []
    assert len(EqualHighDetector(tolerance=2, symbol="USDJPY").detect(jpy_levels)) == 1


def test_user_example_2_pips_forms_equal_highs():
    # High 1 = 1.25002, High 2 = 1.25005, diff = 0.00003. Tolerance is
    # configurable in pips.
    levels = [
        make_level(1.25002, LiquidityType.SWING_HIGH),
        make_level(1.25005, LiquidityType.SWING_HIGH),
    ]

    clusters = EqualHighDetector(tolerance=2, symbol="EURUSD").detect(levels)

    assert len(clusters) == 1  # become equal highs
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
