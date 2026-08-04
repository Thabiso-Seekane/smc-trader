"""Market-structure visualizer.

A debugging tool that renders detected swings and their labels as an
interactive Plotly chart. This module is intentionally **not** used by
the strategy; it exists for developers to verify the analysis algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from structure.enums import StructureLabel, SwingType
from structure.models import MarketStructure


@dataclass(slots=True)
class StructureVisualizer:
    """Renders a Plotly chart of a market structure."""

    def build_figure(self, structure: MarketStructure, candles: pd.DataFrame | None = None) -> go.Figure:
        """Build an interactive Plotly figure for the given structure.

        Args:
            structure: The market structure to render.
            candles: Optional OHLC frame used as the background candlestick
                chart. When omitted, only the swing points are plotted.

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

        for point in structure.points:
            is_high = point.swing_type == SwingType.HIGH
            series = "High" if is_high else "Low"
            color = "#2ca02c" if point.label in (StructureLabel.HH, StructureLabel.HL) else "#d62728"
            symbol = "triangle-up" if is_high else "triangle-down"

            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp],
                    y=[point.price],
                    mode="markers+text",
                    text=[point.label.value],
                    textposition="top center" if is_high else "bottom center",
                    marker={"symbol": symbol, "size": 12, "color": color},
                    name=f"{series} {point.label.value}",
                )
            )

        fig.update_layout(
            title="Market Structure",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def render(self, structure: MarketStructure, candles: pd.DataFrame | None = None) -> go.Figure:
        """Render the market structure as a Plotly figure.

        Convenience wrapper around :meth:`build_figure`.

        Args:
            structure: The market structure to render.
            candles: Optional OHLC frame for the background chart.

        Returns:
            A Plotly ``go.Figure``.
        """
        return self.build_figure(structure, candles)

    def to_html(self, structure: MarketStructure, candles: pd.DataFrame | None = None) -> str:
        """Return a standalone HTML string of the rendered figure.

        Args:
            structure: The market structure to render.
            candles: Optional OHLC frame for the background chart.

        Returns:
            A full HTML document as a string.
        """
        return self.build_figure(structure, candles).to_html(include_plotlyjs="cdn")


__all__ = ["StructureVisualizer"]
