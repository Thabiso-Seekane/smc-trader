"""Smart Money (CHoCH / BOS) visualizer.

A debugging tool that renders detected structural events as an interactive
Plotly chart. This module is intentionally **not** used by the strategy;
it exists for developers to verify the detection algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from smart_money.enums import Direction, StructureEventType
from smart_money.models import SmartMoneyAnalysis


@dataclass(slots=True)
class SmartMoneyVisualizer:
    """Renders a Plotly chart of CHoCH / BOS structural events."""

    def build_figure(
        self, analysis: SmartMoneyAnalysis, candles: pd.DataFrame | None = None
    ) -> go.Figure:
        """Build an interactive Plotly figure for the given events.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame used as the background candlestick
                chart. When omitted, only the event markers are plotted.

        Returns:
            A Plotly ``go.Figure``.
        """
        fig = go.Figure()

        if candles is not None and not candles.empty:
            fig.add_trace(
                go.Candlestick(
                    x=candles["date"],
                    open=candles["open"],
                    high=candles["high"],
                    low=candles["low"],
                    close=candles["close"],
                    name="Price",
                    showlegend=False,
                )
            )

        for event in analysis.events:
            is_bullish = event.is_bullish
            color = "#2ca02c" if is_bullish else "#d62728"
            symbol = "triangle-up" if is_bullish else "triangle-down"
            label = (
                "Bull CHoCH" if event.is_choch and is_bullish
                else "Bear CHoCH" if event.is_choch
                else "Bull BOS" if is_bullish
                else "Bear BOS"
            )

            fig.add_trace(
                go.Scatter(
                    x=[event.timestamp],
                    y=[event.broken_price],
                    mode="markers+text",
                    text=[label],
                    textposition="top center" if is_bullish else "bottom center",
                    marker={"symbol": symbol, "size": 14, "color": color},
                    name=f"{label} ({event.displacement_strength:.0f})",
                    customdata=[event.displacement_strength],
                    hovertemplate=(
                        f"%{{text}}<br>Broken: %{{y:.5f}}"
                        f"<br>Displacement: %{{customdata[0]:.1f}}<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title="CHoCH / BOS Structural Events",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def render(
        self, analysis: SmartMoneyAnalysis, candles: pd.DataFrame | None = None
    ) -> go.Figure:
        """Render the structural events as a Plotly figure.

        Convenience wrapper around :meth:`build_figure`.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.

        Returns:
            A Plotly ``go.Figure``.
        """
        return self.build_figure(analysis, candles)

    def to_html(
        self, analysis: SmartMoneyAnalysis, candles: pd.DataFrame | None = None
    ) -> str:
        """Return a standalone HTML string of the rendered figure.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.

        Returns:
            A full HTML document as a string.
        """
        return self.build_figure(analysis, candles).to_html(include_plotlyjs="cdn")


__all__ = ["SmartMoneyVisualizer"]
