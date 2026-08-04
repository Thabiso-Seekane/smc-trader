"""Unit tests for the Plotly-based market structure visualizer."""

import pandas as pd

from structure.analyzer import MarketStructureAnalyzer
from structure.visualizer import StructureVisualizer


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


def test_render_returns_plotly_figure():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)
    result = MarketStructureAnalyzer().analyze(frame)

    fig = StructureVisualizer().render(result, candles=frame)

    # A Plotly figure has data and layout
    assert hasattr(fig, "to_dict")
    assert len(fig.data) > 0


def test_figure_contains_candlestick_and_markers():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)
    result = MarketStructureAnalyzer().analyze(frame)

    fig = StructureVisualizer().build_figure(result, candles=frame)

    types = [trace.type for trace in fig.data]
    assert "candlestick" in types
    assert "scatter" in types


def test_to_html_returns_standalone_document():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    frame = make_frame(prices)
    result = MarketStructureAnalyzer().analyze(frame)

    html = StructureVisualizer().to_html(result, candles=frame)

    assert "<html" in html.lower()
    assert "plotly" in html.lower()
