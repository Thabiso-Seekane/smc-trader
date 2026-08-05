"""Unit tests for the Smart Money visualizer."""

import pandas as pd
import plotly.graph_objects as go

from smart_money.enums import Direction, StructureEventType
from smart_money.models import SmartMoneyAnalysis, StructureEvent
from smart_money.visualizer import SmartMoneyVisualizer


def candle_frame():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01 00:00", "2024-01-01 00:05", "2024-01-01 00:10"]
            ),
            "open": [1.0, 1.01, 1.02],
            "high": [1.05, 1.06, 1.07],
            "low": [0.95, 0.96, 0.97],
            "close": [1.03, 1.04, 1.05],
            "volume": [100, 110, 120],
        }
    )


def make_analysis():
    choch = StructureEvent(
        event_type=StructureEventType.CHOCH,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:05"),
        broken_price=1.02,
        broken_index=1,
        confirmation_index=2,
        displacement_strength=80.0,
    )
    bos = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BEARISH,
        timestamp=pd.Timestamp("2024-01-01 00:10"),
        broken_price=1.0,
        broken_index=0,
        confirmation_index=2,
        displacement_strength=55.0,
    )
    return SmartMoneyAnalysis(events=[choch, bos])


def test_build_figure_returns_plotly_figure():
    fig = SmartMoneyVisualizer().build_figure(
        make_analysis(), candles=candle_frame()
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_render_without_candles():
    fig = SmartMoneyVisualizer().render(make_analysis())
    assert isinstance(fig, go.Figure)


def test_to_html_returns_string():
    html = SmartMoneyVisualizer().to_html(make_analysis(), candles=candle_frame())
    assert isinstance(html, str)
    assert "<html" in html.lower()
