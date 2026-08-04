"""Unit tests for the public LiquidityAnalyzer façade.

These tests exercise the documented public API using synthetic,
deterministic price data — no MT5 data is used.
"""

import pandas as pd

from liquidity.analyzer import LiquidityAnalyzer
from liquidity.enums import LiquidityType


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


def test_analyze_builds_liquidity_map():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    assert hasattr(result, "levels")
    assert hasattr(result, "clusters")
    assert hasattr(result, "strongest")
    assert hasattr(result, "next_target")
    assert len(result.levels) > 0


def test_map_exposes_buy_and_sell_side():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    assert any(l.is_buy_side for l in result.levels)
    assert any(l.is_sell_side for l in result.levels)


def test_map_contains_swing_liquidity_types():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    types = {l.liquidity_type for l in result.levels}
    assert LiquidityType.SWING_HIGH in types
    assert LiquidityType.SWING_LOW in types


def test_empty_frame_returns_empty_map():
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    result = LiquidityAnalyzer().analyze(empty)

    assert result.levels == []
    assert result.clusters == []
    assert result.strongest is None
    assert result.next_target is None


def test_deterministic_output():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)

    a = LiquidityAnalyzer().analyze(frame)
    b = LiquidityAnalyzer().analyze(frame)

    assert len(a.levels) == len(b.levels)
    assert [l.price for l in a.levels] == [l.price for l in b.levels]


def test_next_target_returns_an_active_level():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    if result.next_target is not None:
        assert result.next_target.swept is False
