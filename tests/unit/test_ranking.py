"""Unit tests for liquidity ranking (5-factor, 0-100 model)."""

from datetime import datetime, timedelta

from liquidity.enums import LiquidityType
from liquidity.models import LiquidityLevel
from liquidity.ranking import LiquidityRanker


def make_level(price, liquidity_type, timestamp=None, timeframe="", swing_index=None):
    return LiquidityLevel(
        price=price,
        liquidity_type=liquidity_type,
        timestamp=timestamp,
        timeframe=timeframe,
        swing_index=swing_index,
    )


def test_equal_highs_ranked_stronger_than_single_swing():
    equal = make_level(100.0, LiquidityType.EQUAL_HIGHS)
    swing = make_level(150.0, LiquidityType.SWING_HIGH)

    ranked = LiquidityRanker().rank([swing, equal])

    assert ranked[0] is equal
    assert ranked[0].strength > ranked[1].strength


def test_scores_are_within_0_100_range():
    levels = [
        make_level(100.0, LiquidityType.SWING_LOW),
        make_level(150.0, LiquidityType.EQUAL_LOWS),
        make_level(200.0, LiquidityType.SWING_HIGH),
    ]

    ranked = LiquidityRanker().rank(levels)

    for level in ranked:
        assert 0.0 <= level.strength <= 100.0


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


def test_recent_level_scores_higher_than_old_level():
    recent = make_level(
        100.0,
        LiquidityType.SWING_HIGH,
        timestamp=datetime.utcnow() - timedelta(days=1),
    )
    old = make_level(
        100.0,
        LiquidityType.SWING_HIGH,
        timestamp=datetime.utcnow() - timedelta(days=100),
    )

    recent.strength = LiquidityRanker()._score(recent)
    old.strength = LiquidityRanker()._score(old)
    assert recent.strength > old.strength


def test_higher_timeframe_scores_higher():
    h1 = make_level(100.0, LiquidityType.SWING_HIGH, timeframe="H1")
    m15 = make_level(100.0, LiquidityType.SWING_HIGH, timeframe="M15")

    h1.strength = LiquidityRanker()._score(h1)
    m15.strength = LiquidityRanker()._score(m15)
    assert h1.strength > m15.strength


def test_next_target_picks_nearest_active():
    strong_far = make_level(200.0, LiquidityType.EQUAL_HIGHS)
    weak_near = make_level(120.0, LiquidityType.SWING_HIGH)

    target = LiquidityRanker().next_target([strong_far, weak_near], current_price=100.0)
    assert target is weak_near


def test_next_target_none_when_all_swept():
    swept = make_level(100.0, LiquidityType.SWING_HIGH)
    swept.swept = True
    assert LiquidityRanker().next_target([swept], current_price=100.0) is None
