"""Unit tests for the public LiquidityMap API.

Exercises the documented Week 3 public API:

    liquidity = liquidity_engine.analyze(df, structure)
    print(liquidity.buy_side)
    print(liquidity.sell_side)
    print(liquidity.equal_highs)
    print(liquidity.sweeps)
"""

import pandas as pd

from liquidity.analyzer import LiquidityAnalyzer
from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap


def make_frame(prices):
    """Build a synthetic OHLC frame from a list of close prices."""
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


def test_map_exposes_buy_side_and_sell_side():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    assert hasattr(result, "buy_side")
    assert hasattr(result, "sell_side")
    assert hasattr(result, "equal_highs")
    assert hasattr(result, "equal_lows")
    assert hasattr(result, "sweeps")


def test_map_queries_return_lists():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    assert isinstance(result.buy_side(), list)
    assert isinstance(result.sell_side(), list)
    assert isinstance(result.equal_highs, list)
    assert isinstance(result.equal_lows, list)
    assert isinstance(result.sweeps, list)


def test_map_contains_swing_high_types():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    types = {l.liquidity_type for l in result.levels}
    assert LiquidityType.SWING_HIGH in types


def test_map_containts_swept_levels_in_sweeps():
    # A simple up-then-down series should produce a swept swing high.
    prices = [100, 101, 102, 103, 104, 101, 100]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    assert result.sweeps == result.swept_levels


def test_empty_frame_returns_empty_map():
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    result = LiquidityAnalyzer().analyze(empty)

    assert result.buy_side() == []
    assert result.sell_side() == []
    assert result.equal_highs == []
    assert result.sweeps == []


def test_level_defaults_to_internal_scope():
    level = LiquidityLevel(price=1.1000, liquidity_type=LiquidityType.SWING_HIGH)
    assert level.scope == LiquidityScope.INTERNAL
    assert level.is_internal is True
    assert level.is_external is False


def test_level_can_be_external_scope():
    level = LiquidityLevel(
        price=1.1000,
        liquidity_type=LiquidityType.RANGE_HIGH,
        scope=LiquidityScope.EXTERNAL,
    )
    assert level.scope == LiquidityScope.EXTERNAL
    assert level.is_external is True
    assert level.is_internal is False


def test_map_partitions_external_and_internal():
    external = LiquidityLevel(
        price=1.1000,
        liquidity_type=LiquidityType.RANGE_HIGH,
        scope=LiquidityScope.EXTERNAL,
    )
    internal = LiquidityLevel(
        price=1.0900,
        liquidity_type=LiquidityType.SWING_LOW,
        scope=LiquidityScope.INTERNAL,
    )
    swept_external = LiquidityLevel(
        price=1.1100,
        liquidity_type=LiquidityType.RANGE_LOW,
        scope=LiquidityScope.EXTERNAL,
        swept=True,
    )
    result = LiquidityMap(levels=[external, internal, swept_external])

    assert result.external_levels == [external, swept_external]
    assert result.internal_levels == [internal]
    assert result.external() == result.external_levels
    assert result.internal() == result.internal_levels
    assert result.external_sweeps == [swept_external]
    assert result.internal_sweeps == []


def test_analyzer_marks_swings_internal_and_ranges_external():
    # A bounded oscillation (range height 0.10 = 10 pips for XAUUSD) should
    # produce internal swing levels plus external range-high/range-low levels.
    prices = [
        100.00, 100.05, 100.10, 100.05, 100.00, 100.05, 100.10,
        100.05, 100.00, 100.05, 100.10, 100.05, 100.00, 100.05,
        100.10, 100.05, 100.00,
    ]
    result = LiquidityAnalyzer(
        lookback=2, tolerance=20, symbol="XAUUSD"
    ).analyze(make_frame(prices))

    assert any(l.is_internal for l in result.levels)
    assert len(result.range_levels) >= 2
    assert all(l.is_external for l in result.range_levels)
