"""Unit tests for liquidity ranking."""

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityLevel
from liquidity.ranking import LiquidityRanker


def make_level(price, liquidity_type, timestamp=None):
    return LiquidityLevel(price=price, liquidity_type=liquidity_type, timestamp=timestamp)


def test_equal_highs_ranked_stronger_than_single_swing():
    equal = make_level(100.0, LiquidityType.EQUAL_HIGHS)
    swing = make_level(150.0, LiquidityType.SWING_HIGH)

    ranked = LiquidityRanker().rank([swing, equal])

    assert ranked[0] is equal
    assert ranked[0].strength > ranked[1].strength


def test_rank_sorts_descending_by_strength():
    levels = [
        make_level(100.0, LiquidityType.SWING_LOW),
        make_level(150.0, LiquidityType.EQUAL_LOWS),
        make_level(200.0, LiquidityType.SWING_HIGH),
    ]

    ranked = LiquidityRanker().rank(levels)

    strengths = [l.strength for l in ranked]
    assert strengths == sorted(strengths, reverse=True)


def test_strongest_returns_highest_ranked():
    equal = make_level(100.0, LiquidityType.EQUAL_LOWS)
    swing = make_level(150.0, LiquidityType.SWING_HIGH)

    strongest = LiquidityRanker().strongest([swing, equal])
    assert strongest is equal


def test_strongest_none_when_empty():
    assert LiquidityRanker().strongest([]) is None


def test_swept_levels_are_de_weighted():
    swept = make_level(100.0, LiquidityType.EQUAL_HIGHS)
    swept.swept = True
    active = make_level(99.0, LiquidityType.SWING_HIGH)

    ranked = LiquidityRanker().rank([swept, active])
    assert ranked[0] is active


def test_next_target_picks_nearest_active():
    strong_far = make_level(200.0, LiquidityType.EQUAL_HIGHS)
    weak_near = make_level(120.0, LiquidityType.SWING_HIGH)

    target = LiquidityRanker().next_target([strong_far, weak_near], current_price=100.0)
    assert target is weak_near


def test_next_target_none_when_all_swept():
    swept = make_level(100.0, LiquidityType.SWING_HIGH)
    swept.swept = True
    assert LiquidityRanker().next_target([swept], current_price=100.0) is None
