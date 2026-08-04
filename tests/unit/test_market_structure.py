"""Unit tests for the public MarketStructureAnalyzer façade.

These tests exercise the documented public API using synthetic,
deterministic price data — no MT5 data is used.
"""

import pandas as pd

from structure.analyzer import MarketStructureAnalyzer
from structure.enums import StructureLabel, Trend


def make_frame(prices):
    """Build a synthetic OHLC frame from a list of prices."""
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


def test_public_api_usage_pattern():
    # exercises exactly the documented usage
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    analyzer = MarketStructureAnalyzer()

    market_structure = analyzer.analyze(make_frame(prices))

    assert hasattr(market_structure, "trend")
    assert hasattr(market_structure, "swings")
    assert hasattr(market_structure, "structure")


def test_analysis_detects_known_swings():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = MarketStructureAnalyzer().analyze(make_frame(prices))

    swing_indices = [s.index for s in result.swings]
    assert swing_indices == [2, 4, 6]


def test_structure_exposes_classified_points():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = MarketStructureAnalyzer().analyze(make_frame(prices))

    assert len(result.structure) == len(result.swings)
    assert result.structure == result.points


def test_empty_frame_returns_empty_structure():
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    result = MarketStructureAnalyzer().analyze(empty)

    assert result.swings == []
    assert result.structure == []
    assert result.trend == Trend.RANGE


def test_deterministic_output():
    # same input always yields the same output
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)

    a = MarketStructureAnalyzer().analyze(frame)
    b = MarketStructureAnalyzer().analyze(frame)

    assert [s.index for s in a.swings] == [s.index for s in b.swings]
    assert a.trend == b.trend
    assert [p.label for p in a.structure] == [p.label for p in b.structure]


def test_history_exposes_order_of_structure_labels():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = MarketStructureAnalyzer().analyze(make_frame(prices))

    history = result.history

    assert history.labels == [StructureLabel.HH, StructureLabel.LL, StructureLabel.HH]
    assert len(history) == len(result.points)


def test_history_latest_returns_most_recent_point():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = MarketStructureAnalyzer().analyze(make_frame(prices))

    latest = result.history.latest

    assert latest is not None
    assert (latest.index, latest.price) == (6, 104.0)
    assert latest.label == StructureLabel.HH


def test_history_empty_when_no_structure():
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    result = MarketStructureAnalyzer().analyze(empty)

    assert result.history.is_empty
    assert result.history.labels == []
    assert result.history.latest is None
