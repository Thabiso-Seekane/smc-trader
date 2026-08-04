"""Unit tests for the liquidity visualizer."""

import pandas as pd

from liquidity.analyzer import LiquidityAnalyzer
from liquidity.visualizer import LiquidityVisualizer


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


def test_build_figure_returns_plotly_figure():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    fig = LiquidityVisualizer().build_figure(result, candles=make_frame(prices))

    assert fig is not None
    assert len(fig.data) > 0


def test_render_returns_figure():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    fig = LiquidityVisualizer().render(result)
    assert fig.layout.title.text == "Liquidity Map — Buy Side / Sell Side"


def test_to_html_returns_html_string():
    prices = [100, 101, 102, 101, 99, 103, 104, 103, 102]
    result = LiquidityAnalyzer().analyze(make_frame(prices))

    html = LiquidityVisualizer().to_html(result)
    assert isinstance(html, str)
    assert html.startswith("<")
