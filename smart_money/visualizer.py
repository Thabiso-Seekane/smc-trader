"""Smart Money (CHoCH / BOS) visualizer.

A debugging tool that renders detected structural events as an interactive
Plotly chart. This module is intentionally **not** used by the strategy;
it exists for developers to verify the detection algorithms.

The chart shows:

    * Optional OHLC candlesticks (background).
    * Optional market-structure labels (HH / HL / LL / LH).
    * Optional liquidity sweeps (buy-side and sell-side).
    * CHoCH events (green up-triangles for bullish, red down-triangles for
      bearish).
    * BOS events (green up-arrows for bullish, red down-arrows for bearish).

Each event type uses a distinct marker and label so the engineer can
quickly distinguish a change of character from a break of structure.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from liquidity.models import LiquidityMap
from smart_money.enums import Direction, StructureEventType
from smart_money.models import SmartMoneyAnalysis
from structure.models import MarketStructure


@dataclass(slots=True)
class SmartMoneyVisualizer:
    """Renders a Plotly chart of CHoCH / BOS structural events."""

    def build_figure(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Build an interactive Plotly figure for the given events.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame used as the background candlestick
                chart. When omitted, only the event markers are plotted.
            structure: Optional market structure whose labelled swing points
                (HH/HL/LH/LL) are drawn.
            liquidity: Optional liquidity map whose swept levels are drawn.

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

        if structure is not None:
            self._add_structure_labels(fig, structure)

        if liquidity is not None:
            self._add_liquidity_sweeps(fig, liquidity)

        for event in analysis.events:
            self._add_event_marker(fig, event)

        fig.update_layout(
            title="CHoCH / BOS Structural Events",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def _add_structure_labels(
        self, fig: go.Figure, structure: MarketStructure
    ) -> None:
        """Plot HH/HL/LH/LL labels above/below each classified swing point."""
        for point in structure.points:
            is_high = point.swing_type.value.lower() == "high"
            label_value = _label_value(point.label)
            color = "#2ca02c" if label_value in ("HH", "HL") else "#d62728"
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp],
                    y=[point.price],
                    mode="markers+text",
                    text=[label_value],
                    textposition="top center" if is_high else "bottom center",
                    marker={"symbol": "circle", "size": 8, "color": color},
                    name=f"Structure {label_value}",
                    showlegend=False,
                    hovertemplate=(
                        f"{label_value}<br>Price: %{{y:.5f}}<extra></extra>"
                    ),
                )
            )

    def _add_liquidity_sweeps(
        self, fig: go.Figure, liquidity: LiquidityMap
    ) -> None:
        """Plot swept buy-side and sell-side liquidity with distinct markers."""
        for level in liquidity.swept_levels:
            if level.timestamp is None:
                continue
            if level.is_buy_side:
                marker = "diamond"
                color = "#9467bd"
                label = "BS Sweep"
            else:
                marker = "hexagon"
                color = "#ff7f0e"
                label = "SS Sweep"
            fig.add_trace(
                go.Scatter(
                    x=[level.timestamp],
                    y=[level.price],
                    mode="markers+text",
                    text=[label],
                    textposition="top right",
                    marker={"symbol": marker, "size": 12, "color": color},
                    name=label,
                    showlegend=False,
                    hovertemplate=(
                        f"{label}<br>Price: %{{y:.5f}}<extra></extra>"
                    ),
                )
            )

    def _add_event_marker(self, fig: go.Figure, event) -> None:
        """Add a single CHoCH / BOS marker to the figure."""
        is_bullish = event.is_bullish
        is_choch = event.is_choch

        if is_choch:
            color = "#2ca02c" if is_bullish else "#d62728"
            symbol = "triangle-up" if is_bullish else "triangle-down"
            label = "Bull CHoCH" if is_bullish else "Bear CHoCH"
        else:
            color = "#17becf" if is_bullish else "#d62728"
            symbol = "arrow-up" if is_bullish else "arrow-down"
            label = "Bull BOS" if is_bullish else "Bear BOS"

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

    def render(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Render the structural events as a Plotly figure.

        Convenience wrapper around :meth:`build_figure`.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

        Returns:
            A Plotly ``go.Figure``.
        """
        return self.build_figure(analysis, candles, structure, liquidity)

    def to_html(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> str:
        """Return a standalone HTML string of the rendered figure.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

        Returns:
            A full HTML document as a string.
        """
        fig = self.build_figure(analysis, candles, structure, liquidity)
        return fig.to_html(include_plotlyjs="cdn")


def _label_value(label) -> str:
    """Normalize a structure label (enum member or raw string) to its value."""
    return label.value if hasattr(label, "value") else str(label)


__all__ = ["SmartMoneyVisualizer"]
