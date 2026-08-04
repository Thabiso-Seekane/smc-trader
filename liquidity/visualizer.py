"""Liquidity visualizer.

A debugging tool that renders a LiquidityMap as an interactive Plotly
chart showing buy-side and sell-side liquidity zones. This module is
intentionally **not** used by the strategy; it exists for developers to
verify the liquidity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from liquidity.models import LiquidityLevel, LiquidityMap


@dataclass(slots=True)
class LiquidityVisualizer:
    """Renders a Plotly chart of the liquidity map."""

    def build_figure(
        self,
        liquidity_map: LiquidityMap,
        candles: pd.DataFrame | None = None,
    ) -> go.Figure:
        """Build an interactive Plotly figure for the given liquidity map.

        Args:
            liquidity_map: The liquidity map to render.
            candles: Optional OHLC frame used as the background candlestick
                chart. When omitted, only the liquidity levels are plotted.

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

        for level in liquidity_map.levels:
            color = self._color_for(level)
            dash = "dot" if level.swept else "solid"
            opacity = 0.3 if level.swept else 0.7

            fig.add_hline(
                y=level.price,
                line_color=color,
                line_dash=dash,
                opacity=opacity,
                annotation_text=level.label or f"{level.liquidity_type.value} @ {level.price:.5f}",
                annotation_position="right" if level.is_buy_side else "left",
            )

        next_target = liquidity_map.next_target
        if next_target is not None:
            fig.add_hline(
                y=next_target.price,
                line_color="gold",
                line_width=3,
                annotation_text=f"→ TARGET @ {next_target.price:.5f}",
                annotation_position="bottom right",
            )

        fig.update_layout(
            title="Liquidity Map — Buy Side / Sell Side",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def render(
        self,
        liquidity_map: LiquidityMap,
        candles: pd.DataFrame | None = None,
    ) -> go.Figure:
        """Render the liquidity map as a Plotly figure.

        Convenience wrapper around :meth:`build_figure`.
        """
        return self.build_figure(liquidity_map, candles)

    def to_html(
        self,
        liquidity_map: LiquidityMap,
        candles: pd.DataFrame | None = None,
    ) -> str:
        """Return a standalone HTML string of the rendered figure.

        Args:
            liquidity_map: The liquidity map to render.
            candles: Optional OHLC frame for the background chart.

        Returns:
            A full HTML document as a string.
        """
        return self.build_figure(liquidity_map, candles).to_html(
            include_plotlyjs="cdn"
        )

    @staticmethod
    def _color_for(level: LiquidityLevel) -> str:
        """Return a CSS colour for the level based on its type and sweep status."""
        if level.swept:
            return "gray"
        if level.is_buy_side:
            return "#d62728"  # red — BSL above price
        return "#2ca02c"  # green — SSL below price


__all__ = ["LiquidityVisualizer"]

