"""Unit tests for range liquidity detection."""

import pandas as pd
import pytest

from liquidity.enums import LiquidityType
from liquidity.range_detector import RangeDetector
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


def range_prices():
    """Build a bounded oscillation series (height 0.10 = 10 pips XAUUSD)."""
    return [
        100.00, 100.05, 100.10, 100.05, 100.00, 100.05, 100.10,
        100.05, 100.00, 100.05, 100.10, 100.05, 100.00, 100.05,
        100.10, 100.05, 100.00,
    ]


def test_detects_range_from_oscillation():
    # Oscillating prices between 100.00 and 100.10 form a bounded range
    # (height 0.10 = 10 pips for XAUUSD, within the 20-pip tolerance).
    structure = MarketStructureAnalyzer().analyze(make_frame(range_prices()))

    levels = RangeDetector(tolerance=20, symbol="XAUUSD").detect(structure)

    assert len(levels) == 2
    types = {l.liquidity_type for l in levels}
    assert LiquidityType.RANGE_HIGH in types
    assert LiquidityType.RANGE_LOW in types


def test_range_high_is_buy_side_and_range_low_is_sell_side():
    structure = MarketStructureAnalyzer().analyze(make_frame(range_prices()))

    levels = RangeDetector(tolerance=20, symbol="XAUUSD").detect(structure)

    range_high = [l for l in levels if l.liquidity_type == LiquidityType.RANGE_HIGH]
    range_low = [l for l in levels if l.liquidity_type == LiquidityType.RANGE_LOW]

    assert range_high[0].is_buy_side
    assert range_low[0].is_sell_side


def test_no_range_when_trending():
    # Monotonic increasing prices are a trend, not a range.
    prices = [100 + i for i in range(20)]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = RangeDetector(tolerance=20, symbol="XAUUSD").detect(structure)
    assert levels == []


def test_no_range_when_insufficient_swings():
    structure = MarketStructureAnalyzer().analyze(make_frame([100, 101, 100]))
    levels = RangeDetector().detect(structure)
    assert levels == []


def test_range_wider_than_tolerance_is_rejected():
    # Range height ~1.0 for XAUUSD with tolerance 5 pips (0.05) is too wide.
    prices = [100, 101, 100, 101, 100, 101, 100, 101, 100]
    structure = MarketStructureAnalyzer().analyze(make_frame(prices))

    levels = RangeDetector(tolerance=5, symbol="XAUUSD").detect(structure)
    assert levels == []


def test_empty_structure_returns_no_levels():
    assert RangeDetector().detect(None) == []
