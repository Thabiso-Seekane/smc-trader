"""Unit tests for the liquidity detector using synthetic, deterministic data."""

import pandas as pd

from liquidity.detector import LiquidityDetector
from liquidity.enums import LiquidityType
from structure.analyzer import MarketStructureAnalyzer


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


def test_detects_swing_liquidity_from_structure():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = LiquidityDetector(timeframe="M15").detect(structure)

    # swings at indices 2 (high), 4 (low), 6 (high)
    assert len(levels) == 3
    highs = [l for l in levels if l.is_buy_side]
    lows = [l for l in levels if l.is_sell_side]
    assert len(highs) == 2
    assert len(lows) == 1


def test_swing_highs_become_buy_side_liquidity():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = LiquidityDetector().detect(structure)
    swing_highs = [l for l in levels if l.liquidity_type == LiquidityType.SWING_HIGH]

    assert len(swing_highs) == 2
    assert all(l.swing_index in (2, 6) for l in swing_highs)
    assert all(l.price in (102.0, 104.0) for l in swing_highs)


def test_swing_lows_become_sell_side_liquidity():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = LiquidityDetector().detect(structure)
    swing_lows = [l for l in levels if l.liquidity_type == LiquidityType.SWING_LOW]

    assert len(swing_lows) == 1
    assert swing_lows[0].price == 99.0
    assert swing_lows[0].swing_index == 4


def test_empty_structure_returns_no_levels():
    assert LiquidityDetector().detect(None) == []


def test_timeframe_label_is_attached():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = LiquidityDetector(timeframe="H1").detect(structure)
    assert all(l.timeframe == "H1" for l in levels)
